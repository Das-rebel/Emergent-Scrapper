import React, { useState, useEffect } from 'react';
import { scraperAPI } from '../api';
import { 
  Activity, 
  Settings, 
  Play, 
  Pause, 
  RotateCcw, 
  TrendingUp,
  MessageSquare,
  Image,
  Video,
  Calendar,
  Users,
  Clock,
  AlertCircle
} from 'lucide-react';
import { format, formatDistanceToNow } from 'date-fns';
import toast, { Toaster } from 'react-hot-toast';

const Dashboard = () => {
  const [analytics, setAnalytics] = useState(null);
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [config, setConfig] = useState(null);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [analyticsRes, schedulerRes, sessionsRes, configRes] = await Promise.all([
        scraperAPI.getAnalytics().catch(() => ({ data: {} })),
        scraperAPI.getSchedulerStatus().catch(() => ({ data: {} })),
        scraperAPI.getSessions(5).catch(() => ({ data: [] })),
        scraperAPI.getConfig().catch(() => ({ data: {} }))
      ]);
      
      setAnalytics(analyticsRes.data);
      setSchedulerStatus(schedulerRes.data);
      setSessions(sessionsRes.data);
      setConfig(configRes.data);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleRunScraping = async () => {
    try {
      toast.loading('Starting scraping session...', { id: 'scraping' });
      await scraperAPI.runScraping();
      toast.success('Scraping session started!', { id: 'scraping' });
      // Refresh data after a short delay
      setTimeout(fetchDashboardData, 2000);
    } catch (error) {
      console.error('Error running scraping:', error);
      toast.error('Failed to start scraping session', { id: 'scraping' });
    }
  };

  const handleToggleScheduler = async () => {
    try {
      if (schedulerStatus?.running) {
        await scraperAPI.stopScheduler();
        toast.success('Scheduler stopped');
      } else {
        await scraperAPI.startScheduler();
        toast.success('Scheduler started');
      }
      fetchDashboardData();
    } catch (error) {
      console.error('Error toggling scheduler:', error);
      toast.error('Failed to toggle scheduler');
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Toaster position="top-right" />
      
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-6">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Twitter Scraper Dashboard</h1>
              <p className="mt-1 text-sm text-gray-500">Monitor and manage your Twitter bookmark scraping</p>
            </div>
            <div className="flex space-x-3">
              <button
                onClick={handleRunScraping}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors"
              >
                <Play className="h-4 w-4" />
                <span>Run Scraping</span>
              </button>
              <button
                onClick={handleToggleScheduler}
                className={`px-4 py-2 rounded-lg flex items-center space-x-2 transition-colors ${
                  schedulerStatus?.running 
                    ? 'bg-red-600 hover:bg-red-700 text-white' 
                    : 'bg-green-600 hover:bg-green-700 text-white'
                }`}
              >
                {schedulerStatus?.running ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
                <span>{schedulerStatus?.running ? 'Stop Scheduler' : 'Start Scheduler'}</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <MessageSquare className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Tweets</p>
                <p className="text-2xl font-bold text-gray-900">
                  {analytics?.total_tweets?.toLocaleString() || 0}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <TrendingUp className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Quality Score</p>
                <p className="text-2xl font-bold text-gray-900">
                  {analytics?.avg_quality_score ? (analytics.avg_quality_score * 100).toFixed(1) + '%' : '0%'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Activity className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Avg Engagement</p>
                <p className="text-2xl font-bold text-gray-900">
                  {analytics?.avg_engagement_score ? (analytics.avg_engagement_score * 100).toFixed(1) + '%' : '0%'}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Scheduler</p>
                <p className="text-2xl font-bold text-gray-900">
                  {schedulerStatus?.running ? 'Running' : 'Stopped'}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Recent Sessions */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-8">
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Recent Scraping Sessions</h3>
            </div>
            <div className="p-6">
              {sessions.length > 0 ? (
                <div className="space-y-4">
                  {sessions.map((session) => (
                    <div key={session.id} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                      <div>
                        <p className="font-medium text-gray-900">
                          {session.tweets_processed} tweets processed
                        </p>
                        <p className="text-sm text-gray-500">
                          {formatDistanceToNow(new Date(session.started_at), { addSuffix: true })}
                        </p>
                      </div>
                      <div className="flex items-center">
                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${
                          session.status === 'completed' 
                            ? 'bg-green-100 text-green-800'
                            : session.status === 'failed'
                            ? 'bg-red-100 text-red-800'
                            : 'bg-yellow-100 text-yellow-800'
                        }`}>
                          {session.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <AlertCircle className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No scraping sessions yet</p>
                </div>
              )}
            </div>
          </div>

          {/* Sentiment Distribution */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Sentiment Distribution</h3>
            </div>
            <div className="p-6">
              {analytics?.sentiment_distribution && Object.keys(analytics.sentiment_distribution).length > 0 ? (
                <div className="space-y-3">
                  {Object.entries(analytics.sentiment_distribution).map(([sentiment, count]) => (
                    <div key={sentiment} className="flex items-center justify-between">
                      <span className="capitalize text-gray-700">{sentiment}</span>
                      <div className="flex items-center space-x-2">
                        <div className="w-24 bg-gray-200 rounded-full h-2">
                          <div 
                            className={`h-2 rounded-full ${
                              sentiment === 'positive' ? 'bg-green-500' :
                              sentiment === 'negative' ? 'bg-red-500' : 'bg-gray-500'
                            }`}
                            style={{ 
                              width: `${Math.min(100, (count / analytics.total_tweets) * 100)}%` 
                            }}
                          ></div>
                        </div>
                        <span className="text-sm font-medium text-gray-900">{count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8">
                  <TrendingUp className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500">No sentiment data available</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Top Categories */}
        {analytics?.top_categories && analytics.top_categories.length > 0 && (
          <div className="bg-white rounded-lg shadow mb-8">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Top Categories</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {analytics.top_categories.slice(0, 6).map((category, index) => (
                  <div key={category.category} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                    <div className="flex-shrink-0">
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white text-sm font-medium ${
                        index === 0 ? 'bg-yellow-500' :
                        index === 1 ? 'bg-gray-400' :
                        index === 2 ? 'bg-orange-600' : 'bg-blue-500'
                      }`}>
                        {index + 1}
                      </div>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">
                        {category.category}
                      </p>
                      <p className="text-sm text-gray-500">
                        {category.count} tweets
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Configuration */}
        {config && (
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b border-gray-200">
              <h3 className="text-lg font-semibold text-gray-900">Configuration</h3>
            </div>
            <div className="p-6">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-sm font-medium text-gray-600">Schedule Interval</p>
                  <p className="text-lg font-semibold text-gray-900">{config.schedule_interval}s</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Max Retries</p>
                  <p className="text-lg font-semibold text-gray-900">{config.max_retries}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-600">Batch Size</p>
                  <p className="text-lg font-semibold text-gray-900">{config.batch_size}</p>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard;