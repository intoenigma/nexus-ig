class ResponseTemplates:
    """Dynamic Hinglish response builder working from user inputs without hardcoded scripts."""

    @classmethod
    def get_greeting(cls, user_name: str, text: str = "") -> str:
        return f"Hey @{user_name}!"

    @classmethod
    def get_status(cls, user_name: str, text: str = "") -> str:
        return f"@{user_name} {text.strip()}"

    @classmethod
    def get_pagal(cls, user_name: str, text: str = "") -> str:
        return f"@{user_name} {text.strip()}"

    @classmethod
    def get_banter(cls, user_name: str, text: str = "") -> str:
        return f"@{user_name} {text.strip()}"

    @classmethod
    def get_fallback(cls, user_name: str, text: str = "") -> str:
        return f"@{user_name} {text.strip()}"


