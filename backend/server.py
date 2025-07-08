from fastapi import FastAPI, APIRouter, HTTPException, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pathlib import Path
import os
import logging
from typing import List, Optional
from datetime import datetime
import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import atexit

# Import our models and services
from .models import (
    StatusCheck, StatusCheckCreate, ProcessedTweet, ScrapingSession, 
    TweetSearchParams, TweetAnalyticsResponse, ScrapingConfig,
    ScrapingSessionResponse
)
from .database import database
from .scraper import TwitterScraper

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create the main app
app = FastAPI(title="Twitter Scraper API", version="1.0.0")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize scheduler
scheduler = AsyncIOScheduler()

# Global scraper instance
scraper_instance = None

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize database and scheduler on startup"""
    global scraper_instance
    
    # Connect to database
    await database.connect()
    logger.info("Database connected")
    
    # Initialize scraper
    scraper_instance = TwitterScraper()
    
    # Setup scheduler
    interval = int(os.environ.get('SCRAPER_SCHEDULE_INTERVAL', '3600'))
    scheduler.add_job(
        run_scheduled_scraping,
        IntervalTrigger(seconds=interval),
        id='scraper_job',
        replace_existing=True
    )
    
    scheduler.start()
    logger.info(f"Scheduler started with {interval}s interval")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    await database.close()
    scheduler.shutdown()
    logger.info("Application shutdown complete")

# Background scraping function
async def run_scheduled_scraping():
    """Run scraping as a background task"""
    try:
        logger.info("Starting scheduled scraping session")
        async with TwitterScraper() as scraper:
            session = await scraper.run_scraping_session()
            logger.info(f"Scheduled scraping completed: {session.tweets_processed} tweets processed")
    except Exception as e:
        logger.error(f"Scheduled scraping failed: {e}")

# Original endpoints
@api_router.get("/")
async def root():
    return {"message": "Twitter Scraper API is running"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await database.db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await database.db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Scraper endpoints
@api_router.post("/scraper/run", response_model=ScrapingSession)
async def run_scraping_session(background_tasks: BackgroundTasks):
    """Manually trigger a scraping session"""
    try:
        async with TwitterScraper() as scraper:
            session = await scraper.run_scraping_session()
            return session
    except Exception as e:
        logger.error(f"Manual scraping failed: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")

@api_router.get("/scraper/sessions", response_model=List[ScrapingSession])
async def get_scraping_sessions(limit: int = 10):
    """Get recent scraping sessions"""
    try:
        sessions = await database.get_recent_sessions(limit)
        return sessions
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch sessions: {str(e)}")

@api_router.get("/scraper/session/{session_id}", response_model=ScrapingSession)
async def get_scraping_session(session_id: str):
    """Get a specific scraping session"""
    try:
        session = await database.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except Exception as e:
        logger.error(f"Error fetching session {session_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch session: {str(e)}")

@api_router.post("/tweets/search", response_model=List[ProcessedTweet])
async def search_tweets(params: TweetSearchParams):
    """Search tweets with filters"""
    try:
        tweets = await database.search_tweets(params)
        return tweets
    except Exception as e:
        logger.error(f"Error searching tweets: {e}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@api_router.get("/tweets/{tweet_id}", response_model=ProcessedTweet)
async def get_tweet(tweet_id: str):
    """Get a specific tweet"""
    try:
        tweet = await database.get_tweet(tweet_id)
        if not tweet:
            raise HTTPException(status_code=404, detail="Tweet not found")
        return tweet
    except Exception as e:
        logger.error(f"Error fetching tweet {tweet_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch tweet: {str(e)}")

@api_router.get("/analytics", response_model=TweetAnalyticsResponse)
async def get_analytics():
    """Get tweet analytics"""
    try:
        analytics = await database.get_tweet_analytics()
        return TweetAnalyticsResponse(**analytics)
    except Exception as e:
        logger.error(f"Error fetching analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics: {str(e)}")

@api_router.get("/tweets", response_model=List[ProcessedTweet])
async def get_tweets(
    limit: int = 50,
    offset: int = 0,
    author: Optional[str] = None,
    category: Optional[str] = None,
    sentiment: Optional[str] = None,
    has_media: Optional[bool] = None
):
    """Get tweets with optional filters"""
    try:
        params = TweetSearchParams(
            limit=limit,
            offset=offset,
            author=author,
            category=category,
            sentiment=sentiment,
            has_media=has_media
        )
        tweets = await database.search_tweets(params)
        return tweets
    except Exception as e:
        logger.error(f"Error fetching tweets: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch tweets: {str(e)}")

@api_router.get("/config", response_model=ScrapingConfig)
async def get_scraper_config():
    """Get current scraper configuration"""
    return ScrapingConfig(
        enabled=scheduler.running,
        schedule_interval=int(os.environ.get('SCRAPER_SCHEDULE_INTERVAL', '3600')),
        max_retries=int(os.environ.get('SCRAPER_MAX_RETRIES', '3')),
        retry_delay=int(os.environ.get('SCRAPER_RETRY_DELAY', '30')),
        batch_size=int(os.environ.get('SCRAPER_BATCH_SIZE', '50'))
    )

@api_router.post("/config", response_model=ScrapingConfig)
async def update_scraper_config(config: ScrapingConfig):
    """Update scraper configuration"""
    try:
        # Update environment variables (in production, this would be persisted)
        os.environ['SCRAPER_SCHEDULE_INTERVAL'] = str(config.schedule_interval)
        os.environ['SCRAPER_MAX_RETRIES'] = str(config.max_retries)
        os.environ['SCRAPER_RETRY_DELAY'] = str(config.retry_delay)
        os.environ['SCRAPER_BATCH_SIZE'] = str(config.batch_size)
        
        # Update scheduler
        if config.enabled and not scheduler.running:
            scheduler.start()
        elif not config.enabled and scheduler.running:
            scheduler.shutdown()
        
        # Update job interval
        scheduler.reschedule_job(
            'scraper_job',
            trigger=IntervalTrigger(seconds=config.schedule_interval)
        )
        
        return config
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update config: {str(e)}")

@api_router.post("/scheduler/start")
async def start_scheduler():
    """Start the scheduler"""
    try:
        if not scheduler.running:
            scheduler.start()
        return {"message": "Scheduler started"}
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start scheduler: {str(e)}")

@api_router.post("/scheduler/stop")
async def stop_scheduler():
    """Stop the scheduler"""
    try:
        if scheduler.running:
            scheduler.shutdown()
        return {"message": "Scheduler stopped"}
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop scheduler: {str(e)}")

@api_router.get("/scheduler/status")
async def get_scheduler_status():
    """Get scheduler status"""
    return {
        "running": scheduler.running,
        "jobs": len(scheduler.get_jobs()),
        "next_run": scheduler.get_job('scraper_job').next_run_time.isoformat() if scheduler.get_job('scraper_job') else None
    }

# Include the router in the main app
app.include_router(api_router)
