from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
import os
import logging
from datetime import datetime
# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
class GenerateRequest(BaseModel):
    text: str
    style: str = "fantasy"
    api_key: Optional[str] = None
# Стили (15 вариантов)
STYLES = {
    "business": {"name": "Бизнес", "prompt": "professional corporate style, clean lines, modern"},
    "creative": {"name": "Креативный", "prompt": "artistic, imaginative, colorful, abstract"},
    "minimalist": {"name": "Минимализм", "prompt": "minimalist design, simple lines, monochrome"},
    "infographic": {"name": "Инфографика", "prompt": "infographic style, data visualization"},
    "playful": {"name": "Игривый", "prompt": "fun, cartoonish, bright colors, friendly"},
    "3d_render": {"name": "3D Рендер", "prompt": "3D render, Blender style, cinematic lighting"},
    "watercolor": {"name": "Акварель", "prompt": "watercolor painting, soft edges, artistic"},
    "cyberpunk": {"name": "Киберпанк", "prompt": "cyberpunk aesthetic, neon lights, futuristic"},
    "flat_design": {"name": "Плоский дизайн", "prompt": "flat design, vector illustration"},
    "oil_painting": {"name": "Масляная живопись", "prompt": "oil painting style, textured brush strokes"},
    "pixel_art": {"name": "Пиксель-арт", "prompt": "pixel art, retro gaming style, 8-bit"},
    "anime": {"name": "Аниме", "prompt": "anime style, Japanese animation, vibrant colors"},
    "sketch": {"name": "Эскиз", "prompt": "sketch drawing, pencil lines, artistic"},
    "vintage": {"name": "Винтаж", "prompt": "vintage style, retro aesthetic, nostalgic"},
    "fantasy": {"name": "Фэнтези", "prompt": "fantasy art, magical creatures, mystical"}
}
@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
@app.get("/styles")
def get_styles():
    styles_list = []
    for key, value in STYLES.items():
        styles_list.append({
            "id": key,
            "name": value["name"],
            "description": value["prompt"]
        })
    return {"styles": styles_list, "total": len(styles_list)}
@app.post("/generate")
def generate(request: GenerateRequest):
    logger.info("=== НАЧАЛО GENERATE ===")
    logger.info(f"Текст: {request.text}")
    logger.info(f"Стиль: {request.style}")
    logger.info(f"API ключ предоставлен: {bool(request.api_key)}")
    # Проверка стиля
    if request.style not in STYLES:
        available_styles = list(STYLES.keys())
        logger.error(f"Неверный стиль: {request.style}. Доступные: {available_styles}")
        return {
            "status": "error",
            "error": f"Неверный стиль. Доступные: {available_styles}",
            "available_styles": available_styles
        }
    # Отключаем proxy
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
    os.environ['NO_PROXY'] = '*'
    # Демо режим
    if not request.api_key:
        logger.info("Режим: ДЕМО")
        return {
            "status": "success",
            "mode": "demo",
            "image_url": "https://images.unsplash.com/photo-1519681393784-d120267933ba?w=1024&h=1024&fit=crop",
            "message": f"Демо: иллюстрация в стиле '{STYLES[request.style]['name']}'",
            "style": request.style,
            "style_name": STYLES[request.style]["name"]
        }
    # OpenAI режим
    logger.info("Режим: OPENAI")
    try:
        client = OpenAI(api_key=request.api_key)
        logger.info("Клиент OpenAI создан")
        prompt = f"{STYLES[request.style]['prompt']}: {request.text}"
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        image_url = response.data[0].url
        logger.info(f"OpenAI успешно: {image_url[:50]}...")
        return {
            "status": "success",
            "mode": "openai",
            "image_url": image_url,
            "message": f"AI иллюстрация в стиле '{STYLES[request.style]['name']}'",
            "style": request.style,
            "style_name": STYLES[request.style]["name"]
        }
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Ошибка OpenAI: {error_msg}")
        # Проверяем ошибку региона
        if 'Country' in error_msg or 'region' in error_msg or 'territory' in error_msg:
            logger.info("Обнаружена ошибка региона")
            return {
                "status": "success",
                "mode": "demo_region_error",
                "image_url": "https://images.unsplash.com/photo-1519681393784-d120267933ba",
                "message": "OpenAI недоступен в вашем регионе. Используется демо-изображение.",
                "error": error_msg,
                "style": request.style,
                "style_name": STYLES[request.style]["name"]
            }
        return {
            "status": "error",
            "mode": "error",
            "error": error_msg,
            "image_url": "https://images.unsplash.com/photo-1519681393784-d120267933ba",
            "style": request.style,
            "style_name": STYLES[request.style]["name"]
        }
# Отключение proxy при запуске
import os
proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'all_proxy', 'ALL_PROXY']
for var in proxy_vars:
    if var in os.environ:
        del os.environ[var]
os.environ['NO_PROXY'] = '*'
if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
