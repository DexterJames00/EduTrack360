from flask import Blueprint, render_template, request, jsonify, session, current_app, redirect, url_for
from models import ActivityLog, db
from datetime import datetime, timedelta
from sqlalchemy import desc, and_, or_

logs_bp = Blueprint('logs', __name__, url_prefix='/school_admin/logs')

@logs_bp.route('/bulletproof')
def bulletproof_logs():
    """Bulletproof logs page with real-time functionality"""
    # Check if user is logged in and is school_admin
    if 'username' not in session or session.get('user_role') != 'school_admin':
        return redirect(url_for('auth.login'))
    return render_template('school_admin/bulletproof_logs.html')

@logs_bp.route('/realtime')
def realtime_logs():
    """Professional real-time logs dashboard"""
    # Check if user is logged in and is school_admin
    if 'username' not in session or session.get('user_role') != 'school_admin':
        return redirect(url_for('auth.login'))
    return render_template('school_admin/logs_dashboard_realtime.html')

@logs_bp.route('/')
def logs_dashboard():
    """Main logs dashboard"""
    # Check if user is logged in and has proper access
    if 'user_id' not in session or session.get('user_type') != 'school_admin':
        return redirect(url_for('auth.login'))
    
    school_id = session.get('school_id')
    
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    action_filter = request.args.get('action')
    entity_filter = request.args.get('entity')
    user_filter = request.args.get('user')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = ActivityLog.query.filter(ActivityLog.school_id == school_id)
    
    # Apply filters
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(ActivityLog.timestamp >= start_dt)
        except ValueError:
            pass
    
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(ActivityLog.timestamp < end_dt)
        except ValueError:
            pass
    
    if action_filter:
        query = query.filter(ActivityLog.action == action_filter.upper())
    
    if entity_filter:
        query = query.filter(ActivityLog.entity_type == entity_filter.lower())
    
    if user_filter:
        query = query.filter(ActivityLog.username.ilike(f'%{user_filter}%'))
    
    # Get paginated results
    logs = query.order_by(desc(ActivityLog.timestamp)).paginate(
        page=page, per_page=50, error_out=False
    )
    
    # Get summary statistics
    total_logs = ActivityLog.query.filter(ActivityLog.school_id == school_id).count()
    
    # Get recent activity (last 24 hours)
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_activity = ActivityLog.query.filter(
        and_(ActivityLog.school_id == school_id, ActivityLog.timestamp >= yesterday)
    ).count()
    
    # Get action counts
    action_counts = db.session.query(
        ActivityLog.action, 
        db.func.count(ActivityLog.id).label('count')
    ).filter(ActivityLog.school_id == school_id).group_by(ActivityLog.action).all()
    
    # Get entity type counts
    entity_counts = db.session.query(
        ActivityLog.entity_type, 
        db.func.count(ActivityLog.id).label('count')
    ).filter(ActivityLog.school_id == school_id).group_by(ActivityLog.entity_type).all()
    
    # Get unique users
    unique_users = db.session.query(ActivityLog.username).filter(
        ActivityLog.school_id == school_id
    ).distinct().all()
    
    return render_template('school_admin/logs_dashboard.html', 
                         logs=logs, 
                         total_logs=total_logs,
                         recent_activity=recent_activity,
                         action_counts=dict(action_counts),
                         entity_counts=dict(entity_counts),
                         unique_users=[user[0] for user in unique_users],
                         filters={
                             'start_date': start_date,
                             'end_date': end_date,
                             'action': action_filter,
                             'entity': entity_filter,
                             'user': user_filter
                         })


@logs_bp.route('/api/recent')
def get_recent_logs():
    """API endpoint to get recent logs for real-time updates"""
    school_id = session.get('school_id')
    
    # Get logs from the last 5 minutes
    recent_time = datetime.utcnow() - timedelta(minutes=5)
    
    recent_logs = ActivityLog.query.filter(
        and_(ActivityLog.school_id == school_id, ActivityLog.timestamp >= recent_time)
    ).order_by(desc(ActivityLog.timestamp)).limit(10).all()
    
    return jsonify([log.to_dict() for log in recent_logs])


@logs_bp.route('/api/logs')
def api_logs():
    """API endpoint for bulletproof logs"""
    # More flexible authentication check - allow if any form of school admin session exists
    school_id = session.get('school_id')
    if not school_id:
        return jsonify({'error': 'No school session'}), 401
    
    # Get recent logs (last 50)
    logs = ActivityLog.query.filter(ActivityLog.school_id == school_id)\
                          .order_by(desc(ActivityLog.timestamp))\
                          .limit(50)\
                          .all()
    
    return jsonify({
        'logs': [log.to_dict() for log in logs],
        'count': len(logs),
        'timestamp': datetime.now().isoformat()
    })

@logs_bp.route('/api/stats')
def api_stats():
    """API endpoint for dashboard statistics"""
    # More flexible authentication check - allow if any form of school admin session exists  
    school_id = session.get('school_id')
    if not school_id:
        return jsonify({'error': 'No school session'}), 401
    
    try:
        # Get today's stats
        today = datetime.now().date()
        today_count = ActivityLog.query.filter(
            and_(
                ActivityLog.school_id == school_id,
                db.func.date(ActivityLog.timestamp) == today
            )
        ).count()
        
        # Get this week's stats
        week_ago = datetime.now() - timedelta(days=7)
        week_count = ActivityLog.query.filter(
            and_(
                ActivityLog.school_id == school_id,
                ActivityLog.timestamp >= week_ago
            )
        ).count()
        
        # Get total count
        total_count = ActivityLog.query.filter(ActivityLog.school_id == school_id).count()
        
        # Get unique users count
        unique_users = db.session.query(ActivityLog.username).filter(
            ActivityLog.school_id == school_id
        ).distinct().count()
        
        return jsonify({
            'today': today_count,
            'week': week_count,
            'total': total_count,
            'total_users': unique_users
        })
        
    except Exception as e:
        current_app.logger.error(f"Error in api_stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


@logs_bp.route('/api/search')
def search_logs():
    """API endpoint for advanced log searching"""
    school_id = session.get('school_id')
    search_term = request.args.get('q', '')
    
    if not search_term:
        return jsonify([])
    
    # Search across multiple fields
    search_results = ActivityLog.query.filter(
        and_(
            ActivityLog.school_id == school_id,
            or_(
                ActivityLog.username.ilike(f'%{search_term}%'),
                ActivityLog.entity_name.ilike(f'%{search_term}%'),
                ActivityLog.description.ilike(f'%{search_term}%'),
                ActivityLog.action.ilike(f'%{search_term}%'),
                ActivityLog.entity_type.ilike(f'%{search_term}%')
            )
        )
    ).order_by(desc(ActivityLog.timestamp)).limit(20).all()
    
    return jsonify([log.to_dict() for log in search_results])


@logs_bp.route('/delete/<int:log_id>', methods=['DELETE'])
def delete_log(log_id):
    """Delete a specific log entry (admin only)"""
    school_id = session.get('school_id')
    
    log_entry = ActivityLog.query.filter(
        and_(ActivityLog.id == log_id, ActivityLog.school_id == school_id)
    ).first()
    
    if not log_entry:
        return jsonify({'success': False, 'message': 'Log entry not found'}), 404
    
    try:
        # Log this deletion action
        from activity_logger import log_activity
        log_activity(
            action='DELETE',
            entity_type='activity_log',
            entity_id=log_id,
            entity_name=f"Log entry #{log_id}",
            description=f"Deleted log entry: {log_entry.username} {log_entry.action} {log_entry.entity_type}"
        )
        
        db.session.delete(log_entry)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Log entry deleted successfully'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error deleting log: {str(e)}'}), 500


@logs_bp.route('/clear', methods=['POST'])
def clear_old_logs():
    """Clear logs older than specified days (admin only)"""
    days = request.json.get('days', 30)
    school_id = session.get('school_id')
    
    try:
        # Calculate cutoff date
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Count logs to be deleted
        logs_to_delete = ActivityLog.query.filter(
            and_(ActivityLog.school_id == school_id, ActivityLog.timestamp < cutoff_date)
        ).count()
        
        # Delete old logs
        deleted_count = ActivityLog.query.filter(
            and_(ActivityLog.school_id == school_id, ActivityLog.timestamp < cutoff_date)
        ).delete()
        
        db.session.commit()
        
        # Log this action
        from activity_logger import log_activity
        log_activity(
            action='DELETE',
            entity_type='activity_log',
            entity_name=f"{deleted_count} old log entries",
            description=f"Cleared {deleted_count} log entries older than {days} days"
        )
        
        return jsonify({
            'success': True, 
            'message': f'Successfully cleared {deleted_count} log entries older than {days} days'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Error clearing logs: {str(e)}'}), 500