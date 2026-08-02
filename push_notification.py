"""
Utilitaire d'envoi de notifications push Web (LCE)
"""
import json
import logging
from flask import current_app
from pywebpush import webpush, WebPushException

logger = logging.getLogger(__name__)


def _get_vapid_claims():
    return {
        'sub': f'mailto:{current_app.config.get("VAPID_CLAIMS_EMAIL", "contact@lcetg.com")}'
    }


def send_push_to_subscription(subscription, title, body, url='/admin/inscriptions',
                               icon='/static/images/lc.JPG', badge='/static/images/lc.JPG',
                               vibrate=None, tag='lce-notif', require_interaction=True,
                               actions=None):
    """Envoie une notification push à une souscription individuelle."""
    if not subscription or not subscription.actif:
        return False

    if vibrate is None:
        vibrate = [200, 100, 200]

    if actions is None:
        actions = [
            {'action': 'view', 'title': "Voir l'inscription"},
            {'action': 'close', 'title': 'Fermer'},
        ]

    payload = {
        'title': title,
        'body': body,
        'icon': icon,
        'badge': badge,
        'vibrate': vibrate,
        'tag': tag,
        'requireInteraction': require_interaction,
        'url': url,
        'actions': actions,
    }

    push_data = {
        'endpoint': subscription.endpoint,
        'keys': {
            'p256dh': subscription.p256dh,
            'auth': subscription.auth,
        }
    }

    vapid_private_key = current_app.config.get('VAPID_PRIVATE_KEY', '')
    vapid_claims = _get_vapid_claims()

    if not vapid_private_key:
        logger.error("VAPID_PRIVATE_KEY non configurée")
        return False

    try:
        webpush(
            subscription_info=push_data,
            data=json.dumps(payload),
            vapid_private_key=vapid_private_key,
            vapid_claims=vapid_claims,
            timeout=10,
        )
        return True
    except WebPushException as e:
        if e.response and e.response.status_code in (404, 410):
            # Souscription invalide → désactiver
            subscription.actif = False
            try:
                from extensions import db
                db.session.commit()
            except Exception:
                pass
            logger.warning(f"Souscription supprimée (gone): {subscription.id}")
        else:
            logger.error(f"Erreur push {subscription.id}: {e}")
        return False
    except Exception as e:
        logger.error(f"Erreur webpush {subscription.id}: {e}")
        return False


def send_push_to_all_admins(title, body, url='/admin/inscriptions', **kwargs):
    """Envoie une notification push à tous les administrateurs abonnés."""
    from models import PushSubscription
    from extensions import db

    subs = PushSubscription.query.filter_by(actif=True).all()
    success = 0
    for sub in subs:
        if send_push_to_subscription(sub, title, body, url=url, **kwargs):
            success += 1
    if success > 0:
        logger.info(f"Push envoyé à {success}/{len(subs)} appareils: {title}")
    return success