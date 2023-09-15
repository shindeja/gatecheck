import requests
import os
import logging

logger = logging.getLogger(__name__)

def http_post_to_webhook(data):
    url = os.environ.get("ALERT_WEBHOOK","")
    alert_key = os.environ.get("ALERT_KEY", "violation")
    if len(url) <= 0:
        logger.warning("Can't send policy violation alerts as no alert webhook URL is set in env var ALERT_WEBHOOK")
        return
    alert_data = {alert_key: data}
    headers = {'Content-Type': 'application/json'}
    try:
        r = requests.post(url, json=alert_data, headers=headers)
    except requests.exceptions.RequestException as e:
        logger.error("Webhook post failed {}".format(e))
        return
    
    logger.info("Webhook post status {}".format(r.status_code))
    return


def handle_webhook_alert(arns, policy_violations):
    alert_message = "Policy violation alert for {} \n ".format(arns)
    for pv in policy_violations:
        alert_message += "Policy violation: {} \n ".format(pv)
    http_post_to_webhook(alert_message)
    return



