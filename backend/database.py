from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING
import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from typing import List, Optional, Dict, Any
from models import ProcessedTweet, ScrapingSession, TweetSearchParams

class Database:
    def __init__(self):
        self.client = None
        self.db = None
        
    async def connect(self):
        mongo_url = os.environ.get('MONGO_URL')
        db_name = os.environ.get('DB_NAME')
        
        self.client = AsyncIOMotorClient(mongo_url)
        self.db = self.client[db_name]
        
        # Create indexes
        await self.create_indexes()
    
    async def create_indexes(self):
        # Tweets collection indexes
        await self.db.tweets.create_index([("id", ASCENDING)], unique=True)
        await self.db.tweets.create_index([("tweet_data.created_at", DESCENDING)])
        await self.db.tweets.create_index([("tweet_data.author", ASCENDING)])
        await self.db.tweets.create_index([("ai_analysis.sentiment.label", ASCENDING)])
        await self.db.tweets.create_index([("ai_analysis.categories", ASCENDING)])
        await self.db.tweets.create_index([("ai_analysis.quality_score", DESCENDING)])
        await self.db.tweets.create_index([("ai_analysis.engagement_prediction", DESCENDING)])
        await self.db.tweets.create_index([("tweet_data.media_features.has_media", ASCENDING)])
        await self.db.tweets.create_index([("tweet_data.media_features.is_thread", ASCENDING)])
        
        # Sessions collection indexes
        await self.db.sessions.create_index([("id", ASCENDING)], unique=True)
        await self.db.sessions.create_index([("started_at", DESCENDING)])
        await self.db.sessions.create_index([("status", ASCENDING)])
    
    async def save_tweet(self, tweet: ProcessedTweet) -> str:
        """Save a processed tweet to the database"""
        tweet_dict = tweet.dict()
        result = await self.db.tweets.update_one(
            {"id": tweet.id},
            {"$set": tweet_dict},
            upsert=True
        )
        return tweet.id
    
    async def get_tweet(self, tweet_id: str) -> Optional[ProcessedTweet]:
        """Get a tweet by ID"""
        doc = await self.db.tweets.find_one({"id": tweet_id})
        if doc:
            return ProcessedTweet(**doc)
        return None
    
    async def search_tweets(self, params: TweetSearchParams) -> List[ProcessedTweet]:
        """Search tweets with filters"""
        query = {}
        
        if params.query:
            query["$text"] = {"$search": params.query}
        
        if params.author:
            query["tweet_data.author"] = {"$regex": params.author, "$options": "i"}
        
        if params.category:
            query["ai_analysis.categories"] = params.category
        
        if params.sentiment:
            query["ai_analysis.sentiment.label"] = params.sentiment
        
        if params.has_media is not None:
            query["tweet_data.media_features.has_media"] = params.has_media
        
        if params.is_thread is not None:
            query["tweet_data.media_features.is_thread"] = params.is_thread
        
        if params.min_quality_score is not None:
            query["ai_analysis.quality_score"] = {"$gte": params.min_quality_score}
        
        if params.min_engagement_score is not None:
            query["ai_analysis.engagement_prediction"] = {"$gte": params.min_engagement_score}
        
        cursor = self.db.tweets.find(query).sort("tweet_data.created_at", -1).skip(params.offset).limit(params.limit)
        tweets = []
        async for doc in cursor:
            tweets.append(ProcessedTweet(**doc))
        
        return tweets
    
    async def get_tweet_analytics(self) -> Dict[str, Any]:
        """Get analytics about tweets"""
        pipeline = [
            {
                "$facet": {
                    "total_stats": [
                        {"$group": {
                            "_id": None,
                            "total_tweets": {"$sum": 1},
                            "avg_quality_score": {"$avg": "$ai_analysis.quality_score"},
                            "avg_engagement_score": {"$avg": "$ai_analysis.engagement_prediction"}
                        }}
                    ],
                    "sentiment_distribution": [
                        {"$group": {
                            "_id": "$ai_analysis.sentiment.label",
                            "count": {"$sum": 1}
                        }}
                    ],
                    "top_categories": [
                        {"$unwind": "$ai_analysis.categories"},
                        {"$group": {
                            "_id": "$ai_analysis.categories",
                            "count": {"$sum": 1}
                        }},
                        {"$sort": {"count": -1}},
                        {"$limit": 10}
                    ],
                    "top_authors": [
                        {"$group": {
                            "_id": "$tweet_data.author",
                            "count": {"$sum": 1},
                            "avg_quality": {"$avg": "$ai_analysis.quality_score"}
                        }},
                        {"$sort": {"count": -1}},
                        {"$limit": 10}
                    ],
                    "media_stats": [
                        {"$group": {
                            "_id": None,
                            "has_images": {"$sum": {"$cond": ["$tweet_data.media_features.has_media", 1, 0]}},
                            "is_thread": {"$sum": {"$cond": ["$tweet_data.media_features.is_thread", 1, 0]}},
                            "youtube_videos": {"$sum": {"$cond": ["$tweet_data.media_features.youtube_video", 1, 0]}}
                        }}
                    ],
                    "daily_stats": [
                        {"$group": {
                            "_id": {"$dateToString": {"format": "%Y-%m-%d", "date": "$tweet_data.created_at"}},
                            "count": {"$sum": 1},
                            "avg_quality": {"$avg": "$ai_analysis.quality_score"}
                        }},
                        {"$sort": {"_id": -1}},
                        {"$limit": 30}
                    ]
                }
            }
        ]
        
        result = await self.db.tweets.aggregate(pipeline).to_list(1)
        
        if result:
            stats = result[0]
            return {
                "total_tweets": stats["total_stats"][0]["total_tweets"] if stats["total_stats"] else 0,
                "avg_quality_score": stats["total_stats"][0]["avg_quality_score"] if stats["total_stats"] else 0.0,
                "avg_engagement_score": stats["total_stats"][0]["avg_engagement_score"] if stats["total_stats"] else 0.0,
                "sentiment_distribution": {item["_id"]: item["count"] for item in stats["sentiment_distribution"]},
                "top_categories": [{"category": item["_id"], "count": item["count"]} for item in stats["top_categories"]],
                "top_authors": [{"author": item["_id"], "count": item["count"], "avg_quality": item["avg_quality"]} for item in stats["top_authors"]],
                "media_stats": stats["media_stats"][0] if stats["media_stats"] else {},
                "daily_stats": [{"date": item["_id"], "count": item["count"], "avg_quality": item["avg_quality"]} for item in stats["daily_stats"]]
            }
        
        return {}
    
    async def save_session(self, session: ScrapingSession) -> str:
        """Save a scraping session"""
        session_dict = session.dict()
        result = await self.db.sessions.update_one(
            {"id": session.id},
            {"$set": session_dict},
            upsert=True
        )
        return session.id
    
    async def get_session(self, session_id: str) -> Optional[ScrapingSession]:
        """Get a scraping session by ID"""
        doc = await self.db.sessions.find_one({"id": session_id})
        if doc:
            return ScrapingSession(**doc)
        return None
    
    async def get_recent_sessions(self, limit: int = 10) -> List[ScrapingSession]:
        """Get recent scraping sessions"""
        cursor = self.db.sessions.find().sort("started_at", -1).limit(limit)
        sessions = []
        async for doc in cursor:
            sessions.append(ScrapingSession(**doc))
        return sessions
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()

# Global database instance
database = Database()