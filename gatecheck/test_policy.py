import json
policy = {
    "task": [
        {
            "attribute": "subnet-type",
            "allowed_values": ["private"],
            "type": "exact",
            "action": "alert"
        },
        {
            "attribute": "subnet-id",
            "allowed_values": [
                "subnet-432190"
            ],
            "type": "exact",
            "action": "alert"
        },
        {
            "attribute": "ip",
            "allowed_values": ["private"],
            "type": "exact",
            "action": "alert"
        },
        {
            "attribute": "image",
            "allowed_values": [".*.dkr.ecr.*.amazonaws.com/*"],
            "type": "pattern",
            "action": "alert"
        },
        {
            "attribute": "enableExecuteCommand",
            "allowed_values": [False],
            "type": "pattern",
            "action": "alert"
        },
        {
            "attribute": "cpu",
            "allowed_values": [256, 4096],
            "type": "range",
            "action": "alert"
        }
    ],
    "service": []
}

print(json.dumps(policy))
