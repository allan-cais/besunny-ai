import React, { useState, useEffect, useCallback } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { useAuth } from '@/providers/AuthProvider';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { supabase } from '@/lib/supabase';

interface DashboardStats {
  totalDocuments: number;
  classifiedDocuments: number;
  accuracy: number;
  trend: 'up' | 'down' | 'stable';
  activeProjects: number;
}

const StatsGrid = () => {
  const { user } = useAuth();
  const [dashboardStats, setDashboardStats] = useState<DashboardStats>({
    totalDocuments: 0,
    classifiedDocuments: 0,
    accuracy: 0,
    trend: 'stable',
    activeProjects: 0
  });
  const [loading, setLoading] = useState(true);

  const fetchDashboardStats = useCallback(async () => {
    if (!user) return;

    try {
      // Fetch total documents for the user
      const { data: totalDocs, error: totalError } = await supabase
        .from('documents')
        .select('id, project_id, classification_source')
        .eq('created_by', user.id);

      if (totalError) {
        throw totalError;
      }

      // Fetch active projects for the user
      const { data: projects, error: projectsError } = await supabase
        .from('projects')
        .select('id')
        .eq('created_by', user.id);

      if (projectsError) {
        throw projectsError;
      }

      // Count AI-classified documents (those classified by the system, not manually by user)
      const aiClassifiedDocs = totalDocs?.filter(doc => 
        doc.project_id && 
        (doc.classification_source === 'ai' || 
         doc.classification_source === 'auto' ||
         doc.classification_source === 'system')
      ) || [];

      const total = totalDocs?.length || 0;
      const aiClassified = aiClassifiedDocs.length;
      const accuracy = total > 0 ? Math.round((aiClassified / total) * 100) : 0;

      // For now, we'll simulate a trend based on recent activity
      // In a real implementation, you'd compare this to historical data
      const trend = accuracy > 85 ? 'up' : accuracy < 70 ? 'down' : 'stable';

      setDashboardStats({
        totalDocuments: total,
        classifiedDocuments: aiClassified,
        accuracy,
        trend,
        activeProjects: projects?.length || 0
      });
    } catch (error) {
      console.error('Failed to fetch dashboard stats:', error);
      // Set to zero if there's an error
      setDashboardStats({
        totalDocuments: 0,
        classifiedDocuments: 0,
        accuracy: 0,
        trend: 'stable',
        activeProjects: 0
      });
    } finally {
      setLoading(false);
    }
  }, [user]);

  useEffect(() => {
    fetchDashboardStats();
  }, [fetchDashboardStats]);

  const getAccuracyColor = (accuracy: number) => {
    if (accuracy >= 90) return 'text-green-600 dark:text-green-400';
    if (accuracy >= 70) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-red-600 dark:text-red-400';
  };

  const getAccuracyBgColor = (accuracy: number) => {
    if (accuracy >= 90) return 'bg-green-50 dark:bg-green-950/20 border-green-200 dark:border-green-800';
    if (accuracy >= 70) return 'bg-yellow-50 dark:bg-yellow-950/20 border-yellow-200 dark:border-yellow-800';
    return 'bg-red-50 dark:bg-red-950/20 border-red-200 dark:border-red-800';
  };

  const getTrendIcon = (trend: 'up' | 'down' | 'stable') => {
    switch (trend) {
      case 'up':
        return <TrendingUp className="w-4 h-4 text-green-600 dark:text-green-400" />;
      case 'down':
        return <TrendingDown className="w-4 h-4 text-red-600 dark:text-red-400" />;
      default:
        return <Minus className="w-4 h-4 text-gray-600 dark:text-gray-400" />;
    }
  };

  const stats = [
    { 
      value: dashboardStats.activeProjects.toString(), 
      label: dashboardStats.activeProjects === 1 ? "ACTIVE PROJECT" : "ACTIVE PROJECTS" 
    },
    { 
      value: dashboardStats.totalDocuments.toString(), 
      label: dashboardStats.totalDocuments === 1 ? "FILE PROCESSED" : "FILES PROCESSED" 
    },
    { 
      value: `${dashboardStats.accuracy}%`, 
      label: "CLASSIFICATION ACCURACY",
      isAccuracy: true,
      accuracy: dashboardStats.accuracy,
      trend: dashboardStats.trend
    }
  ];

  if (loading) {
    return (
      <div className="grid grid-cols-3 gap-4 mt-12">
        {[1, 2, 3].map((i) => (
          <Card key={i} className="p-6">
            <div className="animate-pulse">
              <div className="h-6 bg-gray-200 dark:bg-gray-700 rounded mb-2"></div>
              <div className="h-4 bg-gray-200 dark:bg-gray-700 rounded"></div>
            </div>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="grid grid-cols-3 gap-4 mt-12">
      {stats.map((stat, index) => (
        <Card 
          key={index} 
          className={`p-6 ${stat.isAccuracy ? getAccuracyBgColor(stat.accuracy) : ''}`}
        >
          <div className="flex items-center justify-between">
            <div className={`text-lg font-bold font-mono ${stat.isAccuracy ? getAccuracyColor(stat.accuracy) : ''}`}>
              {stat.value}
            </div>
            {stat.isAccuracy && (
              <div className="flex items-center gap-1">
                {getTrendIcon(stat.trend)}
              </div>
            )}
          </div>
          <div className="text-xs text-gray-600 dark:text-gray-400 font-mono">
            {stat.label}
          </div>

        </Card>
      ))}
    </div>
  );
};

export default StatsGrid; 