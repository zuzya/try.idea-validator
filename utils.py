import re

def extract_json_from_text(text: str):
    """
    Функция-"чистильщик", которая вытаскивает JSON из любого ответа модели.
    """
    try:
        # 1. Пытаемся найти JSON внутри блога кода ```json ... ```
        match = re.search(r"```json\n(.*?)\n```", text, re.DOTALL)
        if match:
            return match.group(1)
        
        # 2. Пытаемся найти JSON внутри обычных скобок { ... }
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        if match:
            return match.group(1)
            
        # 3. Если ничего не нашли, возвращаем как есть (а вдруг там чистый JSON)
        return text
    except Exception:
        return text
