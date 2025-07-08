import React, { useState, useEffect } from 'react';
import { scraperAPI } from '../api';
import { 
  Search, 
  Filter, 
  ExternalLink, 
  Heart, 
  MessageCircle, 
  Share, 
  Image,
  Video,
  Calendar,
  User,
  Tag,
  TrendingUp,
  Brain,
  Eye
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import toast from 'react-hot-toast';

const TweetsList = () => {
  const [tweets, setTweets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    query: '',
    author: '',
    category: '',
    sentiment: '',
    has_media: null,
    is_thread: null,
    min_quality_score: null,
    limit: 20,
    offset: 0
  });
  const [selectedTweet, setSelectedTweet] = useState(null);

  const fetchTweets = async () => {
    try {
      setLoading(true);
      const response = await scraperAPI.getTweets(filters);
      setTweets(response.data);
    } catch (error) {
      console.error('Error fetching tweets:', error);
      toast.error('Failed to load tweets');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTweets();
  }, [filters]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value,
      offset: 0 // Reset pagination when filtering
    }));
  };

  const handleLoadMore = () => {
    setFilters(prev => ({
      ...prev,
      offset: prev.offset + prev.limit
    }));
  };

  const getSentimentColor = (sentiment) => {
    switch (sentiment?.toLowerCase()) {
      case 'positive': return 'text-green-600 bg-green-100';
      case 'negative': return 'text-red-600 bg-red-100';
      default: return 'text-gray-600 bg-gray-100';
    }
  };

  const getQualityColor = (score) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const TweetCard = ({ tweet }) => (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow border border-gray-200">
      <div className="p-6">
        {/* Tweet Header */}
        <div className="flex justify-between items-start mb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
              <User className="h-5 w-5 text-blue-600" />
            </div>
            <div>
              <h3 className="font-semibold text-gray-900">{tweet.tweet_data.author}</h3>
              <p className="text-sm text-gray-500">
                {formatDistanceToNow(new Date(tweet.tweet_data.created_at), { addSuffix: true })}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {tweet.tweet_data.url && (
              <a
                href={tweet.tweet_data.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800"
              >
                <ExternalLink className="h-4 w-4" />
              </a>
            )}
          </div>
        </div>

        {/* Tweet Content */}
        <div className="mb-4">
          <p className="text-gray-800 whitespace-pre-wrap leading-relaxed">
            {tweet.tweet_data.text}
          </p>
        </div>

        {/* Media Indicators */}
        {(tweet.tweet_data.media_features.has_media || tweet.tweet_data.media_features.is_thread) && (
          <div className="flex items-center space-x-2 mb-4">
            {tweet.tweet_data.media_features.has_media && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
                <Image className="h-3 w-3 mr-1" />
                Media
              </span>
            )}
            {tweet.tweet_data.media_features.is_thread && (
              <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
                <MessageCircle className="h-3 w-3 mr-1" />
                Thread
              </span>
            )}
          </div>
        )}

        {/* AI Analysis */}
        {tweet.ai_analysis && (
          <div className="space-y-3 mb-4">
            {/* Sentiment & Quality */}
            <div className="flex items-center space-x-3">
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getSentimentColor(tweet.ai_analysis.sentiment.label)}`}>
                {tweet.ai_analysis.sentiment.label}
              </span>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${getQualityColor(tweet.ai_analysis.quality_score)}`}>
                Quality: {(tweet.ai_analysis.quality_score * 100).toFixed(0)}%
              </span>
              <span className="px-2 py-1 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
                Engagement: {(tweet.ai_analysis.engagement_prediction * 100).toFixed(0)}%
              </span>
            </div>

            {/* Topic */}
            {tweet.ai_analysis.topic && (
              <div>
                <p className="text-sm font-medium text-gray-600 mb-1">Topic:</p>
                <p className="text-sm text-gray-800">{tweet.ai_analysis.topic}</p>
              </div>
            )}

            {/* Categories */}
            {tweet.ai_analysis.categories && tweet.ai_analysis.categories.length > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-600 mb-2">Categories:</p>
                <div className="flex flex-wrap gap-1">
                  {tweet.ai_analysis.categories.slice(0, 3).map((category, index) => (
                    <span key={index} className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-gray-100 text-gray-800">
                      <Tag className="h-3 w-3 mr-1" />
                      {category}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Key Insights */}
            {tweet.ai_analysis.key_insights && tweet.ai_analysis.key_insights.length > 0 && (
              <div>
                <p className="text-sm font-medium text-gray-600 mb-2">Key Insights:</p>
                <ul className="text-sm text-gray-700 space-y-1">
                  {tweet.ai_analysis.key_insights.slice(0, 2).map((insight, index) => (
                    <li key={index} className="flex items-start">
                      <Brain className="h-3 w-3 text-gray-400 mt-1 mr-2 flex-shrink-0" />
                      {insight}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* View Details Button */}
        <button
          onClick={() => setSelectedTweet(tweet)}
          className="w-full mt-4 px-4 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg transition-colors text-sm font-medium"
        >
          <Eye className="h-4 w-4 inline mr-2" />
          View Full Analysis
        </button>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Scraped Tweets</h1>
          <p className="text-gray-600">Browse and analyze your scraped Twitter bookmarks</p>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow mb-8">
          <div className="p-6">
            <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-5 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-gray-400" />
                  <input
                    type="text"
                    placeholder="Search tweets..."
                    value={filters.query}
                    onChange={(e) => handleFilterChange('query', e.target.value)}
                    className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Author</label>
                <input
                  type="text"
                  placeholder="Author name..."
                  value={filters.author}
                  onChange={(e) => handleFilterChange('author', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Sentiment</label>
                <select
                  value={filters.sentiment}
                  onChange={(e) => handleFilterChange('sentiment', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">All Sentiments</option>
                  <option value="positive">Positive</option>
                  <option value="negative">Negative</option>
                  <option value="neutral">Neutral</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Media</label>
                <select
                  value={filters.has_media === null ? '' : filters.has_media.toString()}
                  onChange={(e) => handleFilterChange('has_media', e.target.value === '' ? null : e.target.value === 'true')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">All Tweets</option>
                  <option value="true">With Media</option>
                  <option value="false">Text Only</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Quality</label>
                <select
                  value={filters.min_quality_score || ''}
                  onChange={(e) => handleFilterChange('min_quality_score', e.target.value ? parseFloat(e.target.value) : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="">All Quality</option>
                  <option value="0.8">High Quality (80%+)</option>
                  <option value="0.6">Medium Quality (60%+)</option>
                  <option value="0.4">Low Quality (40%+)</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        {/* Tweets Grid */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">Loading tweets...</p>
          </div>
        ) : tweets.length > 0 ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {tweets.map((tweet) => (
              <TweetCard key={tweet.id} tweet={tweet} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12">
            <MessageCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <p className="text-gray-500">No tweets found matching your criteria</p>
          </div>
        )}

        {/* Load More */}
        {tweets.length > 0 && tweets.length >= filters.limit && (
          <div className="text-center mt-8">
            <button
              onClick={handleLoadMore}
              className="px-6 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
            >
              Load More Tweets
            </button>
          </div>
        )}
      </div>

      {/* Tweet Detail Modal */}
      {selectedTweet && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-screen overflow-y-auto">
            <div className="p-6">
              <div className="flex justify-between items-start mb-4">
                <h3 className="text-lg font-semibold text-gray-900">Tweet Analysis</h3>
                <button
                  onClick={() => setSelectedTweet(null)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  ×
                </button>
              </div>
              
              <div className="space-y-4">
                <div>
                  <h4 className="font-medium text-gray-900 mb-2">Original Tweet</h4>
                  <p className="text-gray-700 bg-gray-50 p-3 rounded">{selectedTweet.tweet_data.text}</p>
                </div>
                
                {selectedTweet.ai_analysis && (
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">AI Analysis</h4>
                    <div className="bg-gray-50 p-4 rounded space-y-3">
                      <div>
                        <span className="font-medium">Topic:</span> {selectedTweet.ai_analysis.topic}
                      </div>
                      <div>
                        <span className="font-medium">Intent:</span> {selectedTweet.ai_analysis.intent}
                      </div>
                      <div>
                        <span className="font-medium">Categories:</span> {selectedTweet.ai_analysis.categories.join(', ')}
                      </div>
                      <div>
                        <span className="font-medium">Entities:</span> {selectedTweet.ai_analysis.entities.join(', ')}
                      </div>
                      <div>
                        <span className="font-medium">Key Insights:</span>
                        <ul className="list-disc list-inside mt-1">
                          {selectedTweet.ai_analysis.key_insights.map((insight, index) => (
                            <li key={index} className="text-sm">{insight}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TweetsList;