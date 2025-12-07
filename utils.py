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

import pathlib
import re

def save_artifact(folder_name: str, filename: str, content: str) -> str:
    """
    Saves content to experiments/<folder_name>/<filename>.
    Handles directory creation and returns the absolute path.
    """
    try:
        # Sanitize folder name
        safe_folder = re.sub(r'[<>:"/\\|?*]', '', folder_name).strip().replace(' ', '_')
        safe_folder = safe_folder[:50] # Limit length
        
        base_dir = pathlib.Path("experiments")
        experiment_dir = base_dir / safe_folder
        experiment_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = experiment_dir / filename
        
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
            
        print(f"   -> [Artifact Saved] {file_path}")
        return str(file_path)
    except Exception as e:
        print(f"   -> [Error Saving Artifact] {e}")
        return ""

