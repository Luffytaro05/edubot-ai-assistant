"""
Usage Statistics Module for EduChat Admin Portal
Provides comprehensive analytics and reporting for chatbot usage across all offices
"""

from flask import Blueprint, request, jsonify, session
from pymongo import MongoClient
from datetime import datetime, timedelta
from bson import ObjectId
import os
from collections import defaultdict
import csv
import io

# Create Blueprint
usage_bp = Blueprint('usage', __name__)

# MongoDB connection (using same connection as main app)
client = MongoClient("mongodb+srv://dxtrzpc26:w1frwdiwmW9VRItO@cluster0.gskdq3p.mongodb.net/")
db = client["chatbot_db"]
conversations_collection = db["conversations"]
feedback_collection = db["feedback"]
users_collection = db["users"]

# Office mappings for performance charts
OFFICES = {
    'guidance': 'Guidance Office',
    'registrar': 'Registrar Office', 
    'admissions': 'Admissions Office',
    'ict': 'ICT Office',
    'osa': 'Office of the Student Affairs(OSA)'
}

class UsageStatsCalculator:
    """Main class for calculating usage statistics"""
    
    def __init__(self):
        self.conversations_collection = conversations_collection
        self.feedback_collection = feedback_collection
        self.users_collection = users_collection
    
    def get_date_range(self, period='daily', start_date=None, end_date=None):
        """Get date range based on period or custom dates"""
        if start_date and end_date:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
                return start, end
            except ValueError:
                # Fallback to default period
                pass
        
        now = datetime.now()
        
        if period == 'daily':
            start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end = start + timedelta(days=1)
        elif period == 'weekly':
            start = now - timedelta(days=7)
            end = now
        elif period == 'monthly':
            start = now - timedelta(days=30)
            end = now
        else:
            # Default to last 7 days
            start = now - timedelta(days=7)
            end = now
            
        return start, end
    
    def get_overview_stats(self, period='daily', start_date=None, end_date=None):
        """Calculate overview statistics"""
        try:
            start_time, end_time = self.get_date_range(period, start_date, end_date)
            
            # Base query for time range
            time_query = {
                'timestamp': {
                    '$gte': start_time,
                    '$lt': end_time
                }
            }
            
            # Total Conversations - count all conversation records
            total_conversations = self.conversations_collection.count_documents(time_query)
            
            # Unique Users - count distinct user IDs
            unique_users = self.conversations_collection.aggregate([
                {'$match': time_query},
                {'$group': {'_id': '$user_id'}},
                {'$count': 'total'}
            ])
            unique_users = list(unique_users)
            unique_users = unique_users[0]['total'] if unique_users else 0
            
            # Average Satisfaction from feedback
            satisfaction_pipeline = [
                {'$match': {
                    'timestamp': {'$gte': start_time, '$lt': end_time},
                    'rating': {'$exists': True, '$ne': None}
                }},
                {'$group': {
                    '_id': None,
                    'avg_rating': {'$avg': '$rating'},
                    'total_ratings': {'$sum': 1}
                }}
            ]
            satisfaction_result = list(self.feedback_collection.aggregate(satisfaction_pipeline))
            avg_satisfaction = satisfaction_result[0]['avg_rating'] if satisfaction_result else 0
            total_ratings = satisfaction_result[0]['total_ratings'] if satisfaction_result else 0
            
            # Resolution Rate - conversations resolved vs escalated
            resolution_pipeline = [
                {'$match': time_query},
                {'$group': {
                    '_id': '$resolved',
                    'count': {'$sum': 1}
                }}
            ]
            resolution_result = list(self.conversations_collection.aggregate(resolution_pipeline))
            
            resolved_count = 0
            total_resolution_conversations = 0
            
            for item in resolution_result:
                total_resolution_conversations += item['count']
                if item['_id'] == True:  # Resolved conversations
                    resolved_count = item['count']
            
            resolution_rate = (resolved_count / total_resolution_conversations * 100) if total_resolution_conversations > 0 else 0
            
            # Calculate trends (comparison with previous period)
            prev_start = start_time - (end_time - start_time)
            prev_end = start_time
            
            prev_stats = self._get_previous_period_stats(prev_start, prev_end)
            trends = self._calculate_trends(
                {
                    'conversations': total_conversations,
                    'users': unique_users,
                    'satisfaction': avg_satisfaction,
                    'resolution': resolution_rate
                },
                prev_stats
            )
            
            return {
                'success': True,
                'data': {
                    'totalConversations': total_conversations,
                    'uniqueUsers': unique_users,
                    'avgSatisfaction': round(avg_satisfaction, 2) if avg_satisfaction else 0,
                    'resolutionRate': round(resolution_rate, 2),
                    'totalRatings': total_ratings,
                    'period': period,
                    'dateRange': {
                        'start': start_time.isoformat(),
                        'end': end_time.isoformat()
                    },
                    'trends': trends
                }
            }
            
        except Exception as e:
            print(f"Error in get_overview_stats: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {
                    'totalConversations': 0,
                    'uniqueUsers': 0,
                    'avgSatisfaction': 0,
                    'resolutionRate': 0,
                    'trends': {}
                }
            }
    
    def get_conversation_trends(self, period='daily', start_date=None, end_date=None, filter_date=None):
        """Get conversation trends over time"""
        try:
            # If single filter_date is provided, use it instead of range
            if filter_date:
                try:
                    filter_dt = datetime.strptime(filter_date, '%Y-%m-%d')
                    start_time = filter_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_time = start_time + timedelta(days=1)
                except ValueError:
                    # Fallback to default range if parsing fails
                    start_time, end_time = self.get_date_range(period, start_date, end_date)
            else:
                start_time, end_time = self.get_date_range(period, start_date, end_date)
            
            # Determine grouping format based on period
            if period == 'daily':
                group_format = '%Y-%m-%d %H:00'  # Group by hour
                date_format = '%H:00'
            elif period == 'weekly':
                group_format = '%Y-%m-%d'  # Group by day
                date_format = '%m/%d'
            else:  # monthly
                group_format = '%Y-%m-%d'  # Group by day
                date_format = '%m/%d'
            
            pipeline = [
                {'$match': {
                    'timestamp': {'$gte': start_time, '$lt': end_time}
                }},
                {'$group': {
                    '_id': {
                        '$dateToString': {
                            'format': group_format,
                            'date': '$timestamp'
                        }
                    },
                    'count': {'$sum': 1}
                }},
                {'$sort': {'_id': 1}}
            ]
            
            results = list(self.conversations_collection.aggregate(pipeline))
            
            # Format results
            labels = []
            values = []
            
            for result in results:
                if period == 'daily':
                    # Convert to readable hour format
                    hour = result['_id'].split(' ')[1]
                    labels.append(hour)
                else:
                    # Convert to readable date format
                    date_obj = datetime.strptime(result['_id'], '%Y-%m-%d')
                    labels.append(date_obj.strftime(date_format))
                
                values.append(result['count'])
            
            return {
                'success': True,
                'data': {
                    'labels': labels,
                    'values': values,
                    'period': period
                }
            }
            
        except Exception as e:
            print(f"Error in get_conversation_trends: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {'labels': [], 'values': []}
            }
    
    def get_office_performance(self, period='daily', start_date=None, end_date=None, filter_date=None):
        """Get performance statistics by office for charts"""
        try:
            # If single filter_date is provided, use it instead of range
            if filter_date:
                try:
                    filter_dt = datetime.strptime(filter_date, '%Y-%m-%d')
                    start_time = filter_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                    end_time = start_time + timedelta(days=1)
                except ValueError:
                    # Fallback to default range if parsing fails
                    start_time, end_time = self.get_date_range(period, start_date, end_date)
            else:
                start_time, end_time = self.get_date_range(period, start_date, end_date)
            
            pipeline = [
                {'$match': {
                    'timestamp': {'$gte': start_time, '$lt': end_time},
                    'office': {'$exists': True, '$ne': None}
                }},
                {'$group': {
                    '_id': '$office',
                    'conversations': {'$sum': 1},
                    'unique_users': {'$addToSet': '$user_id'},
                    'resolved': {'$sum': {'$cond': [{'$eq': ['$resolved', True]}, 1, 0]}},
                    'total_duration': {'$sum': '$duration'}
                }},
                {'$project': {
                    'office': '$_id',
                    'conversations': 1,
                    'unique_users': {'$size': '$unique_users'},
                    'resolution_rate': {
                        '$multiply': [
                            {'$divide': ['$resolved', '$conversations']},
                            100
                        ]
                    },
                    'avg_duration': {'$divide': ['$total_duration', '$conversations']}
                }},
                {'$sort': {'conversations': -1}}
            ]
            
            results = list(self.conversations_collection.aggregate(pipeline))
            
            # Get satisfaction ratings by office
            satisfaction_by_office = self._get_satisfaction_by_office(start_time, end_time)
            
            # Format results
            labels = []
            values = []
            office_details = {}
            
            for result in results:
                office_key = result['office']
                office_name = OFFICES.get(office_key, office_key)
                
                labels.append(office_name)
                values.append(result['conversations'])
                
                office_details[office_key] = {
                    'name': office_name,
                    'conversations': result['conversations'],
                    'users': result['unique_users'],
                    'resolutionRate': round(result.get('resolution_rate', 0), 2),
                    'avgDuration': round(result.get('avg_duration', 0), 2),
                    'satisfaction': satisfaction_by_office.get(office_key, 0)
                }
            
            return {
                'success': True,
                'data': {
                    'labels': labels,
                    'values': values,
                    'details': office_details,
                    'period': period
                }
            }
            
        except Exception as e:
            print(f"Error in get_office_performance: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {'labels': [], 'values': [], 'details': {}}
            }
    
    def get_detailed_statistics(self, period='daily', start_date=None, end_date=None):
        """Get overall detailed statistics (office-specific data removed)"""
        try:
            start_time, end_time = self.get_date_range(period, start_date, end_date)
            
            # Get overall statistics instead of office-specific
            overall_query = {
                'timestamp': {'$gte': start_time, '$lt': end_time}
            }
            
            # Basic conversation stats
            conversations = self.conversations_collection.count_documents(overall_query)
            
            # Unique users
            unique_users_pipeline = [
                {'$match': overall_query},
                {'$group': {'_id': '$user_id'}},
                {'$count': 'total'}
            ]
            unique_users_result = list(self.conversations_collection.aggregate(unique_users_pipeline))
            unique_users = unique_users_result[0]['total'] if unique_users_result else 0
            
            # Average duration
            duration_pipeline = [
                {'$match': overall_query},
                {'$group': {
                    '_id': None,
                    'avg_duration': {'$avg': '$duration'},
                    'total_conversations': {'$sum': 1}
                }}
            ]
            duration_result = list(self.conversations_collection.aggregate(duration_pipeline))
            avg_duration = duration_result[0]['avg_duration'] if duration_result else 0
            
            # Overall satisfaction rating
            satisfaction_query = {
                'timestamp': {'$gte': start_time, '$lt': end_time},
                'rating': {'$exists': True, '$ne': None}
            }
            satisfaction_pipeline = [
                {'$match': satisfaction_query},
                {'$group': {
                    '_id': None,
                    'avg_rating': {'$avg': '$rating'}
                }}
            ]
            satisfaction_result = list(self.feedback_collection.aggregate(satisfaction_pipeline))
            satisfaction = satisfaction_result[0]['avg_rating'] if satisfaction_result else 0
            
            # Overall resolution rate
            resolution_pipeline = [
                {'$match': overall_query},
                {'$group': {
                    '_id': '$resolved',
                    'count': {'$sum': 1}
                }}
            ]
            resolution_result = list(self.conversations_collection.aggregate(resolution_pipeline))
            
            resolved_count = 0
            total_for_resolution = 0
            
            for item in resolution_result:
                total_for_resolution += item['count']
                if item['_id'] == True:
                    resolved_count = item['count']
            
            resolution_rate = (resolved_count / total_for_resolution * 100) if total_for_resolution > 0 else 0
            
            # Calculate trend (comparison with previous period)
            prev_start = start_time - (end_time - start_time)
            prev_end = start_time
            
            prev_conversations = self.conversations_collection.count_documents({
                'timestamp': {'$gte': prev_start, '$lt': prev_end}
            })
            
            trend = 0
            if prev_conversations > 0:
                trend = ((conversations - prev_conversations) / prev_conversations) * 100
            elif conversations > 0:
                trend = 100  # First period with data
            
            detailed_stats = {
                'overall': {
                    'conversations': conversations,
                    'users': unique_users,
                    'avgDuration': round(avg_duration, 2) if avg_duration else 0,
                    'satisfaction': round(satisfaction, 2) if satisfaction else 0,
                    'resolutionRate': round(resolution_rate, 2),
                    'trend': round(trend, 1)
                }
            }
            
            return {
                'success': True,
                'data': detailed_stats,
                'period': period
            }
            
        except Exception as e:
            print(f"Error in get_detailed_statistics: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'data': {}
            }
    
    def export_statistics_csv(self, period='daily', start_date=None, end_date=None):
        """Export statistics to CSV format"""
        try:
            # Get all statistics
            overview = self.get_overview_stats(period, start_date, end_date)
            detailed = self.get_detailed_statistics(period, start_date, end_date)
            office_perf = self.get_office_performance(period, start_date, end_date)
            
            # Create CSV content
            output = io.StringIO()
            writer = csv.writer(output)
            
            # Write header
            writer.writerow(['EduChat Usage Statistics Export'])
            writer.writerow(['Generated:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')])
            writer.writerow(['Period:', period])
            writer.writerow([])
            
            # Overview statistics
            writer.writerow(['OVERVIEW STATISTICS'])
            writer.writerow(['Metric', 'Value'])
            
            if overview['success']:
                data = overview['data']
                writer.writerow(['Total Conversations', data['totalConversations']])
                writer.writerow(['Unique Users', data['uniqueUsers']])
                writer.writerow(['Average Satisfaction', f"{data['avgSatisfaction']}/5.0"])
                writer.writerow(['Resolution Rate', f"{data['resolutionRate']}%"])
            
            writer.writerow([])
            
            # Office performance statistics
            writer.writerow(['OFFICE PERFORMANCE STATISTICS'])
            writer.writerow(['Office', 'Conversations', 'Users', 'Avg Duration (sec)', 'Satisfaction', 'Resolution Rate (%)'])
            
            if office_perf['success']:
                for office_key, stats in office_perf['data']['details'].items():
                    writer.writerow([
                        stats['name'],
                        stats['conversations'],
                        stats['users'],
                        stats['avgDuration'],
                        stats['satisfaction'],
                        stats['resolutionRate']
                    ])
            
            writer.writerow([])
            
            # Overall detailed statistics
            writer.writerow(['OVERALL DETAILED STATISTICS'])
            writer.writerow(['Conversations', 'Users', 'Avg Duration (sec)', 'Satisfaction', 'Resolution Rate (%)', 'Trend (%)'])
            
            if detailed['success'] and 'overall' in detailed['data']:
                stats = detailed['data']['overall']
                writer.writerow([
                    stats['conversations'],
                    stats['users'],
                    stats['avgDuration'],
                    stats['satisfaction'],
                    stats['resolutionRate'],
                    stats['trend']
                ])
            
            csv_content = output.getvalue()
            output.close()
            
            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'usage_statistics_{period}_{timestamp}.csv'
            
            return {
                'success': True,
                'csv': csv_content,
                'filename': filename
            }
            
        except Exception as e:
            print(f"Error in export_statistics_csv: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _get_satisfaction_by_office(self, start_time, end_time):
        """Helper method to get satisfaction ratings by office"""
        pipeline = [
            {'$match': {
                'timestamp': {'$gte': start_time, '$lt': end_time},
                'office': {'$exists': True, '$ne': None},
                'rating': {'$exists': True, '$ne': None}
            }},
            {'$group': {
                '_id': '$office',
                'avg_rating': {'$avg': '$rating'}
            }}
        ]
        
        results = list(self.feedback_collection.aggregate(pipeline))
        
        satisfaction_by_office = {}
        for result in results:
            satisfaction_by_office[result['_id']] = round(result['avg_rating'], 2)
        
        return satisfaction_by_office
    
    def _get_previous_period_stats(self, prev_start, prev_end):
        """Helper method to get statistics for previous period"""
        try:
            time_query = {
                'timestamp': {
                    '$gte': prev_start,
                    '$lt': prev_end
                }
            }
            
            # Previous conversations
            prev_conversations = self.conversations_collection.aggregate([
                {'$match': time_query},
                {'$group': {
                    '_id': {'user_id': '$user_id', 'session_id': '$session_id'},
                    'count': {'$sum': 1}
                }},
                {'$count': 'total'}
            ])
            prev_conversations = list(prev_conversations)
            prev_conversations = prev_conversations[0]['total'] if prev_conversations else 0
            
            # Previous users
            prev_users = self.conversations_collection.aggregate([
                {'$match': time_query},
                {'$group': {'_id': '$user_id'}},
                {'$count': 'total'}
            ])
            prev_users = list(prev_users)
            prev_users = prev_users[0]['total'] if prev_users else 0
            
            # Previous satisfaction
            prev_satisfaction_result = list(self.feedback_collection.aggregate([
                {'$match': {
                    'timestamp': {'$gte': prev_start, '$lt': prev_end},
                    'rating': {'$exists': True, '$ne': None}
                }},
                {'$group': {
                    '_id': None,
                    'avg_rating': {'$avg': '$rating'}
                }}
            ]))
            prev_satisfaction = prev_satisfaction_result[0]['avg_rating'] if prev_satisfaction_result else 0
            
            # Previous resolution rate
            prev_resolution_result = list(self.conversations_collection.aggregate([
                {'$match': time_query},
                {'$group': {
                    '_id': '$resolved',
                    'count': {'$sum': 1}
                }}
            ]))
            
            prev_resolved = 0
            prev_total = 0
            
            for item in prev_resolution_result:
                prev_total += item['count']
                if item['_id'] == True:
                    prev_resolved = item['count']
            
            prev_resolution_rate = (prev_resolved / prev_total * 100) if prev_total > 0 else 0
            
            return {
                'conversations': prev_conversations,
                'users': prev_users,
                'satisfaction': prev_satisfaction,
                'resolution': prev_resolution_rate
            }
            
        except Exception as e:
            print(f"Error getting previous period stats: {str(e)}")
            return {
                'conversations': 0,
                'users': 0,
                'satisfaction': 0,
                'resolution': 0
            }
    
    def _calculate_trends(self, current_stats, previous_stats):
        """Helper method to calculate percentage trends"""
        trends = {}
        
        for key in current_stats:
            current = current_stats[key]
            previous = previous_stats.get(key, 0)
            
            if previous > 0:
                trend = ((current - previous) / previous) * 100
            elif current > 0:
                trend = 100  # New data, 100% increase
            else:
                trend = 0
            
            trends[key] = round(trend, 1)
        
        return trends

# Initialize the calculator
stats_calculator = UsageStatsCalculator()

# API Routes
@usage_bp.route('/api/admin/usage-stats', methods=['GET'])
def get_usage_stats():
    """Main API endpoint for usage statistics"""
    try:
        # Check authentication (Super Admin only)
        auth_result = check_admin_auth()
        if not auth_result['success']:
            return jsonify({
                'success': False,
                'error': auth_result['message']
            }), 401
        
        # Get parameters
        stats_type = request.args.get('type', 'overview')
        period = request.args.get('period', 'daily')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Get additional parameters
        filter_date = request.args.get('filter_date')  # Single date filter for trends
        
        # Route to appropriate function based on type
        if stats_type == 'overview':
            result = stats_calculator.get_overview_stats(period, start_date, end_date)
        elif stats_type == 'trends':
            result = stats_calculator.get_conversation_trends(period, start_date, end_date, filter_date)
        elif stats_type == 'office_performance':
            result = stats_calculator.get_office_performance(period, start_date, end_date, filter_date)
        elif stats_type == 'detailed':
            result = stats_calculator.get_detailed_statistics(period, start_date, end_date)
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid stats type'
            }), 400
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in get_usage_stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@usage_bp.route('/api/admin/usage-stats/export', methods=['GET'])
def export_usage_stats():
    """Export usage statistics to CSV"""
    try:
        # Check authentication (Super Admin only)
        auth_result = check_admin_auth()
        if not auth_result['success']:
            return jsonify({
                'success': False,
                'error': auth_result['message']
            }), 401
        
        # Get parameters
        period = request.args.get('period', 'daily')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Export statistics
        result = stats_calculator.export_statistics_csv(period, start_date, end_date)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error in export_usage_stats: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Helper function to check admin authentication
def check_admin_auth():
    """Check if user is authenticated as admin using JWT token"""
    try:
        # Get Authorization header
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return {
                'success': False,
                'message': 'No valid authorization token provided'
            }
        
        # Extract token
        token = auth_header.split(' ')[1]
        
        # Import JWT and app config
        import jwt
        from flask import current_app
        
        # Decode and verify token
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            
            # Check if user is admin
            if payload.get('role') != 'admin':
                return {
                    'success': False,
                    'message': 'Admin access required'
                }
            
            # Check token expiration
            import datetime
            if datetime.datetime.utcnow().timestamp() > payload.get('exp', 0):
                return {
                    'success': False,
                    'message': 'Token has expired'
                }
            
            return {
                'success': True,
                'user_id': payload.get('user_id'),
                'email': payload.get('email'),
                'role': payload.get('role')
            }
            
        except jwt.ExpiredSignatureError:
            return {
                'success': False,
                'message': 'Token has expired'
            }
        except jwt.InvalidTokenError:
            return {
                'success': False,
                'message': 'Invalid token'
            }
            
    except Exception as e:
        print(f"Authentication error: {str(e)}")
        return {
            'success': False,
            'message': 'Authentication failed'
        }
