import json
policy = {
    "task": [
        {
            "attribute": "subnet",
            "allowed_values": ["private"],
            "type": "exact",
            "action": "terminate"
        },
        {
            "attribute": "ip",
            "allowed_values": ["private"],
            "type": "exact",
            "action": "terminate"
        },
        {
            "attribute": "image",
            "allowed_values": ["foo/*", "bar.us-west-2.*"],
            "type": "pattern",
            "action": "terminate"
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
            "action": "terminate"
        }
    ],
    "service": []
}

