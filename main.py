from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import Optional
from openai import OpenAI
import os
import logging
from datetime import datetime
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Illustraitor AI API",
    description="API для генерации изображений через DALL-E 3",
    version="2.0.0",
    docs_url="/docs",  # Включить Swagger UI
    redoc_url="/redoc"  # Включить ReDoc
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Для разработки
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Модель запроса
class GenerateRequest(BaseModel):
    text: str
    style: str = "fantasy"
    api_key: Optional[str] = None
    size: str = "1024x1024"
    quality: str = "standard"

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

# Демо изображения для разных стилей
DEMO_IMAGES = {
    "business": "https://images.unsplash.com/photo-1497366754035-f200968a6e72",
    "creative": "https://images.unsplash.com/photo-1542744095-fcf48d80b0fd",
    "fantasy": "https://images.unsplash.com/photo-1519681393784-d120267933ba",
    "minimalist": "https://images.unsplash.com/photo-1516035069371-29a1b244cc32",
    "cyberpunk": "https://images.unsplash.com/photo-1518709268805-4e9042af2176",
    "watercolor": "https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5",
    "default": "https://images.unsplash.com/photo-1519681393784-d120267933ba"
}

# ========== КРИТИЧЕСКИ ВАЖНЫЕ ЭНДПОИНТЫ ДЛЯ RENDER ==========

@app.head("/")
async def head_root():
    """
    HEAD запрос для Render health checks
    Render использует HEAD / для проверки доступности
    """
    return

@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = f"""
    <!DOCTYPE html>
    <html lang="ru">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Illustraitor AI API v2.0.0</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                margin: 0;
                padding: 0;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.95);
                border-radius: 20px;
                padding: 40px;
                max-width: 800px;
                width: 90%;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                margin: 20px;
            }}
            h1 {{
                color: #333;
                margin-bottom: 10px;
                font-size: 2.5em;
            }}
            .subtitle {{
                color: #666;
                font-size: 1.1em;
                margin-bottom: 30px;
            }}
            .status {{
                display: inline-block;
                background: #4CAF50;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                margin-bottom: 30px;
            }}
            .endpoints {{
                background: #f8f9fa;
                border-radius: 10px;
                padding: 20px;
                margin: 20px 0;
            }}
            .endpoint {{
                background: white;
                padding: 15px;
                margin: 10px 0;
                border-left: 4px solid #667eea;
                border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.1);
            }}
            .method {{
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 3px 10px;
                border-radius: 3px;
                font-weight: bold;
                margin-right: 10px;
                font-family: monospace;
            }}
            .path {{
                font-family: monospace;
                color: #333;
                font-weight: bold;
            }}
            .links {{
                margin-top: 30px;
                display: flex;
                gap: 15px;
                flex-wrap: wrap;
            }}
            .link {{
                display: inline-block;
                padding: 10px 20px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                transition: transform 0.2s, background 0.2s;
            }}
            .link:hover {{
                background: #764ba2;
                transform: translateY(-2px);
            }}
            .footer {{
                margin-top: 30px;
                color: #666;
                font-size: 0.9em;
                text-align: center;
                border-top: 1px solid #eee;
                padding-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🚀 Illustraitor AI</h1>
            <p class="subtitle">API для генерации изображений через DALL-E 3</p>
            <div class="status">✅ Сервер работает</div>
            
            <div class="endpoints">
                <h2>📚 Доступные эндпоинты:</h2>
                
                <div class="endpoint">
                    <span class="method">GET/HEAD</span>
                    <span class="path">/</span>
                    <p>Эта страница (информация о сервере)</p>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span>
                    <span class="path">/health</span>
                    <p>Проверка работоспособности сервера</p>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span>
                    <span class="path">/styles</span>
                    <p>Получить список доступных стилей генерации</p>
                </div>
                
                <div class="endpoint">
                    <span class="method">POST</span>
                    <span class="path">/generate</span>
                    <p>Сгенерировать изображение по описанию</p>
                </div>
                
                <div class="endpoint">
                    <span class="method">GET</span>
                    <span class="path">/docs</span>
                    <p>Swagger документация API</p>
                </div>
            </div>
            
            <div class="links">
                <a href="/docs" class="link">📖 Swagger документация</a>
                <a href="/redoc" class="link">📚 ReDoc документация</a>
                <a href="/health" class="link">🩺 Health Check</a>
                <a href="/styles" class="link">🎨 Стили</a>
            </div>
            
            <div class="footer">
                <p>Версия: 2.0.0 | Запущено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Использует OpenAI DALL-E 3 API | Хостинг: Render</p>
                <p>Status: <strong style="color: #4CAF50;">● Online</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.get("/health")
async def health_check():
    """
    Health check endpoint для мониторинга Render
    Render проверяет этот эндпоинт каждые несколько секунд
    """
    return JSONResponse({
        "status": "healthy",
        "service": "illustraitor-ai",
        "version": "2.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "environment": os.getenv("ENVIRONMENT", "production"),
        "styles_count": len(STYLES),
        "uptime": "running",
        "endpoints": {
            "root": "/",
            "health": "/health",
            "styles": "/styles",
            "generate": "/generate",
            "docs": "/docs"
        }
    })

# ========== ОСНОВНЫЕ ЭНДПОИНТЫ API ==========

@app.get("/styles")
async def get_styles():
    """Получить список всех доступных стилей генерации"""
    styles_list = []
    for key, value in STYLES.items():
        styles_list.append({
            "id": key,
            "name": value["name"],
            "description": value["prompt"],
            "demo_image": DEMO_IMAGES.get(key, DEMO_IMAGES["default"])
        })
    
    return {
        "status": "success",
        "styles": styles_list, 
        "total": len(styles_list),
        "timestamp": datetime.utcnow().isoformat(),
        "note": "Для генерации используйте POST /generate"
    }

@app.post("/generate")
async def generate(request: GenerateRequest):
    """
    Основной эндпоинт генерации изображений
    Поддерживает два режима: демо (без ключа) и OpenAI (с API ключом)
    """
    start_time = datetime.now()
    request_id = f"req_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.urandom(4).hex()}"
    
    logger.info(f"[{request_id}] === НАЧАЛО GENERATE ===")
    logger.info(f"[{request_id}] Текст: {request.text[:50]}...")
    logger.info(f"[{request_id}] Стиль: {request.style}")
    logger.info(f"[{request_id}] Размер: {request.size}")
    logger.info(f"[{request_id}] API ключ предоставлен: {bool(request.api_key)}")
    
    # Проверка стиля
    if request.style not in STYLES:
        available_styles = list(STYLES.keys())
        logger.error(f"[{request_id}] Неверный стиль: {request.style}. Доступные: {available_styles}")
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "error": f"Неверный стиль. Доступные: {', '.join(available_styles)}",
                "available_styles": available_styles,
                "request_id": request_id
            }
        )
    
    # Очистка proxy переменных (для избежания проблем с подключением)
    proxy_vars = ['http_proxy', 'https_proxy', 'HTTP_PROXY', 'HTTPS_PROXY']
    for var in proxy_vars:
        if var in os.environ:
            del os.environ[var]
    os.environ['NO_PROXY'] = '*'
    
    # Демо режим (если нет API ключа)
    if not request.api_key:
        logger.info(f"[{request_id}] Режим: ДЕМО")
        demo_image = DEMO_IMAGES.get(request.style, DEMO_IMAGES["default"])
        width, height = request.size.split('x')
        
        return {
            "status": "success",
            "mode": "demo",
            "image_url": f"{demo_image}?w={width}&h={height}&fit=crop&auto=format",
            "message": f"Демо-режим: иллюстрация в стиле '{STYLES[request.style]['name']}'",
            "style": request.style,
            "style_name": STYLES[request.style]["name"],
            "size": request.size,
            "generation_time": round((datetime.now() - start_time).total_seconds(), 2),
            "request_id": request_id,
            "note": "Для реальной генерации укажите ваш OpenAI API ключ в поле api_key",
            "documentation": "/docs"
        }
    
    # OpenAI режим
    logger.info(f"[{request_id}] Режим: OPENAI")
    try:
        client = OpenAI(api_key=request.api_key)
        logger.info(f"[{request_id}] Клиент OpenAI создан успешно")
        
        prompt = f"{STYLES[request.style]['prompt']}: {request.text}"
        logger.info(f"[{request_id}] Формированный промпт: {prompt[:100]}...")
        
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt[:4000],  # Ограничение длины промпта
            size=request.size,
            quality=request.quality,
            n=1,
            style="vivid"  # или "natural"
        )
        
        image_url = response.data[0].url
        logger.info(f"[{request_id}] OpenAI успешно: {image_url[:50]}...")
        
        return {
            "status": "success",
            "mode": "openai",
            "image_url": image_url,
            "message": f"AI иллюстрация в стиле '{STYLES[request.style]['name']}'",
            "style": request.style,
            "style_name": STYLES[request.style]["name"],
            "size": request.size,
            "quality": request.quality,
            "generation_time": round((datetime.now() - start_time).total_seconds(), 2),
            "model": "dall-e-3",
            "request_id": request_id,
            "prompt_used": prompt[:200]
        }
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"[{request_id}] Ошибка OpenAI: {error_msg}")
        
        # Автоматический fallback на демо-режим при ошибке
        demo_image = DEMO_IMAGES.get(request.style, DEMO_IMAGES["default"])
        width, height = request.size.split('x')
        
        # Определяем тип ошибки
        error_type = "unknown_error"
        user_message = "Ошибка генерации. Используется демо-изображение."
        
        if 'Country' in error_msg or 'region' in error_msg or 'territory' in error_msg:
            error_type = "region_restriction"
            user_message = "OpenAI недоступен в вашем регионе. Используется демо-изображение."
        elif 'billing' in error_msg or 'quota' in error_msg or 'credit' in error_msg:
            error_type = "billing_issue"
            user_message = "Проблема с балансом API ключа. Используется демо-изображение."
        elif 'authentication' in error_msg or 'invalid' in error_msg or '401' in error_msg:
            error_type = "auth_error"
            user_message = "Неверный API ключ. Используется демо-изображение."
        elif 'rate' in error_msg.lower() or 'limit' in error_msg.lower():
            error_type = "rate_limit"
            user_message = "Превышен лимит запросов. Используется демо-изображение."
        elif 'timeout' in error_msg.lower():
            error_type = "timeout"
            user_message = "Таймаут подключения к OpenAI. Используется демо-изображение."
        
        return {
            "status": "success",  # Успех, потому что вернули fallback
            "mode": "fallback",
            "image_url": f"{demo_image}?w={width}&h={height}&fit=crop&auto=format",
            "message": user_message,
            "error_type": error_type,
            "original_error": error_msg[:200] if len(error_msg) > 200 else error_msg,
            "style": request.style,
            "style_name": STYLES[request.style]["name"],
            "generation_time": round((datetime.now() - start_time).total_seconds(), 2),
            "recovery_strategy": "fallback_to_demo",
            "request_id": request_id,
            "suggestion": "Проверьте API ключ или попробуйте позже"
        }

@app.get("/test-openai")
async def test_openai(api_key: str):
    """
    Проверка работоспособности OpenAI API ключа
    Использование: GET /test-openai?api_key=sk-...
    """
    try:
        client = OpenAI(api_key=api_key)
        models = client.models.list()
        
        # Проверяем доступность DALL-E
        dall_e_available = any('dall' in model.id.lower() for model in models.data)
        
        return {
            "status": "success",
            "message": "OpenAI API ключ работает",
            "models_count": len(models.data),
            "dall_e_available": dall_e_available,
            "organization": getattr(client, 'organization', 'not_set'),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "message": "OpenAI API ключ не работает",
            "timestamp": datetime.utcnow().isoformat()
        }

@app.get("/info")
async def get_info():
    """Информация о сервере и доступных функциях"""
    return {
        "service": "Illustraitor AI",
        "version": "2.0.0",
        "description": "API для генерации изображений через DALL-E 3",
        "features": {
            "styles_count": len(STYLES),
            "modes": ["demo", "openai", "fallback"],
            "demo_images": "Unsplash",
            "ai_model": "OpenAI DALL-E 3",
            "max_prompt_length": 4000
        },
        "endpoints": {
            "GET /": "Главная страница",
            "GET /health": "Проверка состояния",
            "GET /styles": "Список стилей",
            "POST /generate": "Генерация изображения",
            "GET /test-openai": "Проверка API ключа",
            "GET /docs": "Swagger документация",
            "GET /redoc": "ReDoc документация"
        },
        "timestamp": datetime.utcnow().isoformat(),
        "status": "operational"
    }

# ========== СТАРТ СЕРВЕРА ==========
if __name__ == "__main__":
    import uvicorn
    
    # Получаем порт из переменных окружения (Render передает через $PORT)
    port = int(os.environ.get("PORT", 8000))
    
    logger.info("=" * 50)
    logger.info("🚀 Запуск Illustraitor AI API")
    logger.info(f"📌 Порт: {port}")
    logger.info(f"🎨 Стилей: {len(STYLES)}")
    logger.info(f"📚 Документация: http://localhost:{port}/docs")
    logger.info(f"🩺 Health check: http://localhost:{port}/health")
    logger.info("=" * 50)
    
    uvicorn.run(
        app,
        host="0.0.0.0",  # Доступ с любого IP
        port=port,
        log_level="info",
        access_log=True,
        timeout_keep_alive=5
    )
