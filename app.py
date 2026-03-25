from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_wtf.csrf import CSRFProtect, CSRFError
from config import config
from supabase_client import supabase
import os, uuid, logging, bleach
from datetime import datetime, date, timedelta
from functools import wraps       


  

# ════════════════════════════════════════   
#   APP INIT   
# ════════════════════════════════════════
app = Flask(__name__)
app.config.from_object(config['development'])

# Logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s'
)
logger = logging.getLogger(__name__)

# Security extensions
csrf    = CSRFProtect(app)
limiter = Limiter(get_remote_address, app=app, default_limits=["200/day", "100/hour"],
                  storage_uri="memory://")

CSP = {
    'default-src': ["'self'"],
    'script-src':  ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com",
                    "cdn.datatables.net", "code.jquery.com"],
    'style-src':   ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "cdnjs.cloudflare.com",
                    "fonts.googleapis.com", "cdn.datatables.net"],
    'font-src':    ["'self'", "fonts.gstatic.com", "cdnjs.cloudflare.com"],
    'img-src':     ["'self'", "data:", "blob:", "https:", "http:"],
    'connect-src': ["'self'"],
}
talisman = Talisman(app, content_security_policy=CSP, force_https=False,
                    strict_transport_security=False,
                    frame_options='SAMEORIGIN',
                    x_content_type_options=True)

os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'members'), exist_ok=True)
os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'trainers'), exist_ok=True)

# ════════════════════════════════════════
#   HELPERS
# ════════════════════════════════════════
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def sanitize(value, max_length=500):
    """Strip HTML tags and limit length."""
    if not isinstance(value, str):
        return value
    return bleach.clean(value.strip(), tags=[], strip=True)[:max_length]

def get_gym_settings():
    res = supabase.table("gym_settings").select("*").limit(1).execute()
    if res.data:
        return res.data[0]
    return {'gym_name': 'PowerFit Gym', 'gym_address': '', 'gym_phone': '',
            'gym_email': '', 'gym_website': '', 'theme': 'dark', 'currency': '₹', 'gym_logo': None}

def get_next_member_id():
    res = supabase.table("members").select("member_id").order("id", desc=True).limit(1).execute()
    if not res.data:
        return 'GYM001'
    num = int(res.data[0]['member_id'].replace('GYM', ''))
    return f"GYM{(num+1):03d}"

def get_next_invoice():
    res = supabase.table("payments").select("id").order("id", desc=True).limit(1).execute()
    num = res.data[0]['id'] + 1 if res.data else 1
    return f"INV-{datetime.now().year}-{num:03d}"

# ════════════════════════════════════════
#   AUTH DECORATORS
# ════════════════════════════════════════
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'admin':
            flash('Admin access required.', 'danger')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login first.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def member_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if session.get('role') != 'member':
            flash('Please login as a member.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated

def api_protected(f):
    """Require active session for API routes."""
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated

# ════════════════════════════════════════
#   CONTEXT PROCESSOR
# ════════════════════════════════════════
@app.context_processor
def inject_globals():
    open_complaints = 0
    unread_messages = 0
    unread_announcements = 0
    unread_complaint_replies = 0
    current_member_data = None
    total_members = 0
    active_members = 0
    expired_members = 0
    total_revenue = 0

    try:
        if session.get('role') == 'admin':
            open_complaints = len(supabase.table("complaints").select("id").in_("status", ["open","in_progress"]).execute().data or [])
            unread_messages = len(supabase.table("messages").select("id").is_("reply", "null").execute().data or [])
            members_data = supabase.table("members").select("id, status").execute().data or []
            total_members   = len(members_data)
            active_members  = sum(1 for m in members_data if m.get('status') == 'active')
            expired_members = sum(1 for m in members_data if m.get('status') == 'expired')
            payments_data   = supabase.table("payments").select("amount, payment_status").execute().data or []
            total_revenue   = sum(float(p.get('amount', 0)) for p in payments_data if p.get('payment_status') == 'completed')

        elif session.get('role') == 'member':
            uid = session.get('user_id')
            res = supabase.table("members").select("*").eq("id", uid).execute()
            current_member_data = res.data[0] if res.data else None
            all_ann  = supabase.table("announcements").select("id").eq("is_active", True).execute().data or []
            reads    = supabase.table("announcement_reads").select("announcement_id").eq("member_id", uid).execute().data or []
            read_ids = {r['announcement_id'] for r in reads}
            unread_announcements = sum(1 for a in all_ann if a['id'] not in read_ids)
            complaints = supabase.table("complaints").select("status, admin_reply").eq("member_id", uid).execute().data or []
            unread_complaint_replies = sum(1 for c in complaints if c.get('admin_reply') and c.get('status') == 'resolved')
    except Exception as e:
        logger.error("Context processor error: %s", e)

    return dict(
        open_complaints=open_complaints,
        unread_messages=unread_messages,
        unread_announcements=unread_announcements,
        unread_complaint_replies=unread_complaint_replies,
        current_member_data=current_member_data,
        total_members=total_members,
        active_members=active_members,
        expired_members=expired_members,
        total_revenue=total_revenue,
    )

# ════════════════════════════════════════
#   ERROR HANDLERS
# ════════════════════════════════════════
@app.errorhandler(404)
def not_found(e):
    return render_template('login.html', settings=get_gym_settings(),
                           error="Page not found."), 404

@app.errorhandler(500)
def server_error(e):
    logger.error("500 error: %s", e)
    return render_template('login.html', settings=get_gym_settings(),
                           error="Something went wrong. Please try again."), 500

@app.errorhandler(CSRFError)
def csrf_error(e):
    flash('Session expired or invalid request. Please try again.', 'danger')
    return redirect(request.referrer or url_for('login'))

@app.errorhandler(429)
def rate_limit_error(e):
    flash('Too many requests. Please slow down.', 'danger')
    return redirect(url_for('login'))

# ════════════════════════════════════════
#   ROOT
# ════════════════════════════════════════
@app.route('/')
def index():
    if session.get('role') == 'admin':
        return redirect(url_for('dashboard'))
    if session.get('role') == 'member':
        return redirect(url_for('member_dashboard'))
    return render_template('index.html', settings=get_gym_settings())

# ════════════════════════════════════════
#   LOGIN / LOGOUT
# ════════════════════════════════════════
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("5/minute", methods=["POST"])
def login():
    if session.get('role') == 'admin':
        return redirect(url_for('dashboard'))
    if session.get('role') == 'member':
        return redirect(url_for('member_dashboard'))

    if request.method == 'POST':
        identifier = sanitize(request.form.get('identifier', ''))
        password   = request.form.get('password', '')

        if not identifier or not password:
            flash('Please enter both username and password.', 'danger')
            return render_template('login.html', settings=get_gym_settings())

        # Admin login
        res = supabase.table("admins").select("*").eq("username", identifier).execute()
        if res.data:
            admin = res.data[0]
            pwd = admin.get('password_hash') or admin.get('password', '')
            if pwd and check_password_hash(pwd, password):
                session.permanent = True
                session['user_id']  = admin['id']
                session['username'] = admin['username']
                session['full_name']= admin['full_name']
                session['role']     = 'admin'
                logger.info("Admin login: %s from %s", identifier, request.remote_addr)
                flash(f"Welcome back, {admin['full_name']}!", 'success')
                return redirect(url_for('dashboard'))

        # Member login
        res = supabase.table("members").select("*").or_(
            f"member_id.eq.{identifier.upper()},email.eq.{identifier.lower()}"
        ).execute()
        if res.data:
            member = res.data[0]
            pwd = member.get('password_hash') or member.get('password', '')
            if pwd and check_password_hash(pwd, password):
                session.permanent = True
                session['user_id']  = member['id']
                session['member_id']= member['member_id']
                session['full_name']= member['full_name']
                session['role']     = 'member'
                logger.info("Member login: %s from %s", identifier, request.remote_addr)
                flash(f"Welcome back, {member['full_name']}! 💪", 'success')
                return redirect(url_for('member_dashboard'))

        logger.warning("Failed login attempt: %s from %s", identifier, request.remote_addr)
        flash('Invalid credentials.', 'danger')

    return render_template('login.html', settings=get_gym_settings())

@app.route('/logout')
def logout():
    logger.info("Logout: user_id=%s role=%s", session.get('user_id'), session.get('role'))
    session.clear()
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))

# ════════════════════════════════════════
#   ADMIN DASHBOARD
# ════════════════════════════════════════
@app.route('/admin/dashboard')
@admin_required
def dashboard():
    members  = supabase.table("members").select("*").execute().data or []
    payments = supabase.table("payments").select("*").execute().data or []
    today    = date.today().strftime('%Y-%m-%d')

    total_members   = len(members)
    active_members  = sum(1 for m in members if m.get('status') == 'active')
    expired_members = sum(1 for m in members if m.get('status') == 'expired')
    today_payments  = sum(float(p.get('amount', 0)) for p in payments if str(p.get('payment_date',''))[:10] == today)
    total_revenue   = sum(float(p.get('amount', 0)) for p in payments if p.get('payment_status') == 'completed')

    trainers_count = len(supabase.table("trainers").select("id").execute().data or [])
    plans_count    = len(supabase.table("membership_plans").select("id").execute().data or [])

    monthly_data = {}
    for i in range(5, -1, -1):
        d   = date.today().replace(day=1) - timedelta(days=i*28)
        key = d.strftime('%b %Y')
        monthly_data[key] = 0
    for p in payments:
        try:
            pd  = datetime.strptime(str(p['payment_date'])[:10], '%Y-%m-%d')
            key = pd.strftime('%b %Y')
            if key in monthly_data:
                monthly_data[key] += float(p.get('amount', 0))
        except:
            pass

    recent_payments = sorted(payments, key=lambda x: str(x.get('payment_date','')), reverse=True)[:5]
    member_map = {m['id']: m['full_name'] for m in members}
    for p in recent_payments:
        p['member_name'] = member_map.get(p.get('member_id'), 'Unknown')
        p['net_amount']  = p.get('amount', 0)
        if not p.get('invoice_number'):
            p['invoice_number'] = f"INV-{p['id']}"

    expiring_soon = []
    for m in members:
        try:
            exp  = datetime.strptime(str(m['expiry_date'])[:10], '%Y-%m-%d').date()
            diff = (exp - date.today()).days
            if 0 <= diff <= 7:
                expiring_soon.append({**m, 'days_left': diff})
        except:
            pass

    open_complaints = len(supabase.table("complaints").select("id").in_("status", ["open","in_progress"]).execute().data or [])
    open_messages   = len(supabase.table("messages").select("id").is_("reply", "null").execute().data or [])

    return render_template('dashboard.html',
        total_members=total_members, active_members=active_members,
        expired_members=expired_members, today_payments=today_payments,
        total_revenue=total_revenue,
        monthly_labels=list(monthly_data.keys()),
        monthly_values=list(monthly_data.values()),
        recent_payments=recent_payments,
        expiring_soon=expiring_soon,
        trainers_count=trainers_count, plans_count=plans_count,
        open_complaints=open_complaints, open_messages=open_messages,
        unread_messages=open_messages,
        settings=get_gym_settings())

# ════════════════════════════════════════
#   ADMIN — MEMBERS
# ════════════════════════════════════════
@app.route('/admin/members')
@admin_required
def members():
    search        = sanitize(request.args.get('search', ''))
    status_filter = request.args.get('status', '')
    plan_filter   = request.args.get('plan', '')
    page          = int(request.args.get('page', 1))

    query = supabase.table("members").select("*, membership_plans(plan_name), trainers(full_name)")
    if status_filter:
        query = query.eq("status", status_filter)
    if plan_filter:
        query = query.eq("membership_plan_id", plan_filter)

    all_members = query.execute().data or []

    if search:
        s = search.lower()
        all_members = [m for m in all_members if
            s in m.get('full_name','').lower() or
            s in m.get('phone','').lower() or
            s in m.get('member_id','').lower() or
            s in (m.get('email') or '').lower()]

    total      = len(all_members)
    per_page   = app.config['MEMBERS_PER_PAGE']
    total_pages= (total + per_page - 1) // per_page
    start      = (page - 1) * per_page
    paginated  = all_members[start:start + per_page]

    for m in paginated:
        m['plan_name']    = (m.get('membership_plans') or {}).get('plan_name', 'N/A')
        m['trainer_name'] = (m.get('trainers') or {}).get('full_name', 'N/A')

    plans = supabase.table("membership_plans").select("*").execute().data or []

    return render_template('members.html',
        members=paginated, total=total, page=page, total_pages=total_pages,
        search=search, status_filter=status_filter, plan_filter=plan_filter,
        plans=plans, settings=get_gym_settings())

@app.route('/admin/members/add', methods=['GET', 'POST'])
@admin_required
def add_member():
    if request.method == 'POST':
        f    = request.form
        plan_res = supabase.table("membership_plans").select("*").eq("id", f.get('plan_id', 0)).execute()
        plan = plan_res.data[0] if plan_res.data else None

        join_date   = datetime.strptime(f['join_date'], '%Y-%m-%d').date()
        expiry_date = join_date + timedelta(days=30 * (plan['duration_months'] if plan else 1))

        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename and allowed_file(photo.filename):
                photo_filename = f"member_{uuid.uuid4().hex[:8]}.{photo.filename.rsplit('.',1)[1].lower()}"
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], 'members', photo_filename))

        raw_pw = f.get('member_password', '').strip() or f['phone'][-4:]

        new_member = {
            'member_id':         get_next_member_id(),
            'full_name':         sanitize(f['full_name']),
            'phone':             sanitize(f['phone'], 20),
            'email':             sanitize(f.get('email', ''), 200),
            'password_hash':     generate_password_hash(raw_pw),
            'address':           sanitize(f.get('address', '')),
            'date_of_birth':     f.get('date_of_birth') or None,
            'gender':            f.get('gender', ''),
            'photo':             photo_filename,
            'membership_plan_id':int(f['plan_id']) if f.get('plan_id') else None,
            'trainer_id':        int(f['trainer_id']) if f.get('trainer_id') else None,
            'join_date':         f['join_date'],
            'expiry_date':       expiry_date.strftime('%Y-%m-%d'),
            'status':            'active',
            'blood_group':       f.get('blood_group', ''),
            'emergency_contact': sanitize(f.get('emergency_contact', ''), 100),
            'notes':             sanitize(f.get('notes', '')),
        }
        member_res = supabase.table("members").insert(new_member).execute()
        member_id  = member_res.data[0]['id']

        if f.get('plan_id') and f.get('payment_mode') and plan:
            discount   = float(f.get('discount', 0))
            amount     = float(plan['price'])
            net_amount = amount - discount
            supabase.table("payments").insert({
                'invoice_number': get_next_invoice(),
                'member_id':      member_id,
                'plan_id':        int(f['plan_id']),
                'amount':         net_amount,
                'payment_mode':   f['payment_mode'],
                'payment_status': 'completed',
                'payment_date':   f['join_date'],
                'remarks':        sanitize(f.get('payment_notes', '')),
            }).execute()

        logger.info("Member added: %s by admin %s", new_member['member_id'], session.get('username'))
        flash('Member added successfully!', 'success')
        return redirect(url_for('members'))

    plans    = supabase.table("membership_plans").select("*").eq("status", "active").execute().data or []
    trainers = supabase.table("trainers").select("*").eq("status", "active").execute().data or []
    return render_template('add_member.html', plans=plans, trainers=trainers,
                           settings=get_gym_settings(), edit_mode=False, member=None)

@app.route('/admin/members/view/<int:member_id>')
@admin_required
def view_member(member_id):
    res = supabase.table("members").select("*").eq("id", member_id).execute()
    if not res.data:
        flash('Member not found.', 'danger')
        return redirect(url_for('members'))
    member = res.data[0]

    plan = None
    if member.get('membership_plan_id'):
        pr = supabase.table("membership_plans").select("*").eq("id", member['membership_plan_id']).execute()
        plan = pr.data[0] if pr.data else None

    trainer = None
    if member.get('trainer_id'):
        tr = supabase.table("trainers").select("*").eq("id", member['trainer_id']).execute()
        trainer = tr.data[0] if tr.data else None

    member['plan_name']         = plan.get('plan_name', 'N/A') if plan else 'N/A'
    member['trainer_name']      = trainer.get('full_name', 'N/A') if trainer else 'N/A'
    member['membership_status'] = member.get('status', 'active')

    days_left = 0
    try:
        exp = datetime.strptime(str(member['expiry_date'])[:10], '%Y-%m-%d').date()
        days_left = (exp - date.today()).days
    except:
        pass

    attendance = supabase.table("attendance").select("attendance_date").eq("member_id", member_id).execute().data or []
    payments_raw = supabase.table("payments").select("*").eq("member_id", member_id).order("payment_date", desc=True).execute().data or []
    for p in payments_raw:
        p['net_amount'] = p.get('amount', 0)
        p['discount']   = p.get('discount', 0) or 0
        p['valid_from'] = p.get('valid_from') or p.get('payment_date', '')
        p['valid_to']   = p.get('valid_to') or ''
        if not p.get('invoice_number'):
            p['invoice_number'] = f"INV-{p['id']}"

    plans = supabase.table("membership_plans").select("*").execute().data or []

    return render_template('view_member.html', member=member, plan=plan, trainer=trainer,
                           days_left=days_left, attendance=attendance, payments=payments_raw,
                           plans=plans, settings=get_gym_settings())

@app.route('/admin/members/edit/<int:member_id>', methods=['GET', 'POST'])
@admin_required
def edit_member(member_id):
    if request.method == 'POST':
        f = request.form
        data = {
            'full_name':         sanitize(f['full_name']),
            'phone':             sanitize(f['phone'], 20),
            'email':             sanitize(f.get('email', ''), 200),
            'address':           sanitize(f.get('address', '')),
            'date_of_birth':     f.get('date_of_birth') or None,
            'gender':            f.get('gender', ''),
            'membership_plan_id':int(f['plan_id']) if f.get('plan_id') else None,
            'trainer_id':        int(f['trainer_id']) if f.get('trainer_id') else None,
            'blood_group':       f.get('blood_group', ''),
            'emergency_contact': sanitize(f.get('emergency_contact', ''), 100),
            'notes':             sanitize(f.get('notes', '')),
            'status':            f.get('membership_status', 'active'),
        }
        if f.get('new_password'):
            data['password_hash'] = generate_password_hash(f['new_password'])

        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename and allowed_file(photo.filename):
                fname = f"member_{uuid.uuid4().hex[:8]}.{photo.filename.rsplit('.',1)[1].lower()}"
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], 'members', fname))
                data['photo'] = fname

        supabase.table("members").update(data).eq("id", member_id).execute()
        flash('Member updated!', 'success')
        return redirect(url_for('view_member', member_id=member_id))

    res = supabase.table("members").select("*").eq("id", member_id).execute()
    if not res.data:
        flash('Member not found.', 'danger')
        return redirect(url_for('members'))
    member  = res.data[0]
    plans    = supabase.table("membership_plans").select("*").execute().data or []
    trainers = supabase.table("trainers").select("*").execute().data or []
    return render_template('add_member.html', member=member, plans=plans, trainers=trainers,
                           settings=get_gym_settings(), edit_mode=True)

@app.route('/admin/members/delete/<int:member_id>', methods=['POST'])
@admin_required
def delete_member(member_id):
    supabase.table("members").delete().eq("id", member_id).execute()
    logger.info("Member deleted: id=%s by admin %s", member_id, session.get('username'))
    flash('Member deleted.', 'success')
    return redirect(url_for('members'))

# ════════════════════════════════════════
#   ADMIN — ATTENDANCE
# ════════════════════════════════════════
@app.route('/admin/attendance')
@admin_required
def admin_attendance():
    today       = date.today().strftime('%Y-%m-%d')
    date_filter = request.args.get('date', today)
    search      = sanitize(request.args.get('search', ''))

    members = supabase.table("members").select("id, member_id, full_name, phone, status, photo").execute().data or []
    att     = supabase.table("attendance").select("member_id").eq("attendance_date", date_filter).execute().data or []
    present_ids = {a['member_id'] for a in att}

    all_att = supabase.table("attendance").select("member_id").execute().data or []
    visit_counts = {}
    for a in all_att:
        visit_counts[a['member_id']] = visit_counts.get(a['member_id'], 0) + 1

    for m in members:
        m['is_present']        = m['id'] in present_ids
        m['membership_status'] = m.get('status', 'active')
        m['total_visits']      = visit_counts.get(m['id'], 0)

    if search:
        s = search.lower()
        members = [m for m in members if s in m.get('full_name','').lower()
                   or s in m.get('phone','').lower()
                   or s in m.get('member_id','').lower()]

    return render_template('admin_attendance.html',
        members=members, today=today, date_filter=date_filter,
        search=search, total_present=len(present_ids),
        settings=get_gym_settings())

@app.route('/admin/attendance/toggle', methods=['POST'])
@admin_required
def toggle_attendance():
    member_id   = int(request.form['member_id'])
    att_date    = request.form.get('att_date', date.today().strftime('%Y-%m-%d'))
    existing    = supabase.table("attendance").select("id").eq("member_id", member_id).eq("attendance_date", att_date).execute().data
    if existing:
        supabase.table("attendance").delete().eq("id", existing[0]['id']).execute()
    else:
        supabase.table("attendance").insert({'member_id': member_id, 'attendance_date': att_date}).execute()
    logger.info("Attendance toggled: member_id=%s date=%s by admin %s", member_id, att_date, session.get('username'))
    return redirect(url_for('admin_attendance', date=att_date, search=request.form.get('search','')))

# ════════════════════════════════════════
#   ADMIN — TRAINERS
# ════════════════════════════════════════
@app.route('/admin/trainers')
@admin_required
def trainers():
    data = supabase.table("trainers").select("*").execute().data or []
    return render_template('trainers.html', trainers=data, settings=get_gym_settings())

@app.route('/admin/trainers/add', methods=['GET', 'POST'])
@admin_required
def add_trainer():
    if request.method == 'POST':
        f = request.form
        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename and allowed_file(photo.filename):
                photo_filename = f"trainer_{uuid.uuid4().hex[:8]}.{photo.filename.rsplit('.',1)[1].lower()}"
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], 'trainers', photo_filename))
        supabase.table("trainers").insert({
            'full_name':        sanitize(f['full_name']),
            'email':            sanitize(f.get('email', ''), 200),
            'phone':            sanitize(f['phone'], 20),
            'specialization':   sanitize(f.get('specialization', '')),
            'experience_years': int(f.get('experience_years', 0)),
            'bio':              sanitize(f.get('bio', '')),
            'salary':           float(f.get('salary', 0)),
            'join_date':        f['join_date'],
            'photo':            photo_filename,
            'status':           'active',
        }).execute()
        flash('Trainer added!', 'success')
        return redirect(url_for('trainers'))
    return render_template('trainer_form.html', settings=get_gym_settings(), edit_mode=False, trainer=None)

@app.route('/admin/trainers/edit/<int:trainer_id>', methods=['GET', 'POST'])
@admin_required
def edit_trainer(trainer_id):
    if request.method == 'POST':
        f = request.form
        supabase.table("trainers").update({
            'full_name':        sanitize(f['full_name']),
            'email':            sanitize(f.get('email', ''), 200),
            'phone':            sanitize(f['phone'], 20),
            'specialization':   sanitize(f.get('specialization', '')),
            'experience_years': int(f.get('experience_years', 0)),
            'bio':              sanitize(f.get('bio', '')),
            'salary':           float(f.get('salary', 0)),
        }).eq("id", trainer_id).execute()
        flash('Trainer updated!', 'success')
        return redirect(url_for('trainers'))
    res = supabase.table("trainers").select("*").eq("id", trainer_id).execute()
    trainer = res.data[0] if res.data else None
    return render_template('trainer_form.html', settings=get_gym_settings(), edit_mode=True, trainer=trainer)

@app.route('/admin/trainers/delete/<int:trainer_id>', methods=['POST'])
@admin_required
def delete_trainer(trainer_id):
    supabase.table("trainers").delete().eq("id", trainer_id).execute()
    flash('Trainer deleted.', 'success')
    return redirect(url_for('trainers'))

# ════════════════════════════════════════
#   ADMIN — PLANS
# ════════════════════════════════════════
@app.route('/admin/plans')
@admin_required
def plans():
    data = supabase.table("membership_plans").select("*").order("duration_months").execute().data or []
    return render_template('plans.html', plans=data, settings=get_gym_settings())

@app.route('/admin/plans/add', methods=['POST'])
@admin_required
def add_plan():
    f = request.form
    supabase.table("membership_plans").insert({
        'plan_name':       sanitize(f['plan_name']),
        'duration_months': int(f['duration_months']),
        'price':           float(f['price']),
        'description':     sanitize(f.get('description', '')),
        'features':        sanitize(f.get('features', '')),
        'status':          'active',
    }).execute()
    flash('Plan added!', 'success')
    return redirect(url_for('plans'))

@app.route('/admin/plans/edit/<int:plan_id>', methods=['POST'])
@admin_required
def edit_plan(plan_id):
    f = request.form
    supabase.table("membership_plans").update({
        'plan_name':       sanitize(f['plan_name']),
        'duration_months': int(f['duration_months']),
        'price':           float(f['price']),
        'description':     sanitize(f.get('description', '')),
        'features':        sanitize(f.get('features', '')),
    }).eq("id", plan_id).execute()
    flash('Plan updated!', 'success')
    return redirect(url_for('plans'))

@app.route('/admin/plans/delete/<int:plan_id>', methods=['POST'])
@admin_required
def delete_plan(plan_id):
    supabase.table("membership_plans").delete().eq("id", plan_id).execute()
    flash('Plan deleted.', 'success')
    return redirect(url_for('plans'))

# ════════════════════════════════════════
#   ADMIN — PAYMENTS
# ════════════════════════════════════════
@app.route('/admin/payments')
@admin_required
def payments():
    search        = sanitize(request.args.get('search', ''))
    mode_filter   = request.args.get('mode', '')
    status_filter = request.args.get('status', '')

    data = supabase.table("payments").select("*, members(full_name, member_id), membership_plans(plan_name)").order("payment_date", desc=True).execute().data or []

    for p in data:
        p['member_name'] = (p.get('members') or {}).get('full_name', 'N/A')
        p['member_code'] = (p.get('members') or {}).get('member_id', '')
        p['plan_name']   = (p.get('membership_plans') or {}).get('plan_name', 'N/A')
        p['net_amount']  = p.get('amount', 0)
        p['discount']    = 0
        if not p.get('invoice_number'):
            p['invoice_number'] = f"INV-{p['id']}"

    if search:
        s = search.lower()
        data = [p for p in data if s in p['member_name'].lower() or s in p.get('invoice_number','').lower()]
    if mode_filter:
        data = [p for p in data if p.get('payment_mode') == mode_filter]
    if status_filter:
        data = [p for p in data if p.get('payment_status') == status_filter]

    cash_total = sum(float(p.get('amount',0)) for p in data if p.get('payment_mode') == 'Cash')
    upi_total  = sum(float(p.get('amount',0)) for p in data if p.get('payment_mode') == 'UPI')
    card_total = sum(float(p.get('amount',0)) for p in data if p.get('payment_mode') == 'Card')

    members = supabase.table("members").select("id, full_name, member_id").execute().data or []
    plans   = supabase.table("membership_plans").select("*").execute().data or []

    return render_template('payments.html', payments=data,
        cash_total=cash_total, upi_total=upi_total, card_total=card_total,
        search=search, mode_filter=mode_filter, status_filter=status_filter,
        members=members, plans=plans, settings=get_gym_settings())

@app.route('/admin/payments/add', methods=['POST'])
@admin_required
def add_payment():
    f        = request.form
    plan_res = supabase.table("membership_plans").select("*").eq("id", f.get('plan_id', 0)).execute()
    plan     = plan_res.data[0] if plan_res.data else None
    amount   = float(plan['price']) if plan else 0
    valid_to = (datetime.strptime(f['payment_date'], '%Y-%m-%d').date() +
                timedelta(days=30 * (plan['duration_months'] if plan else 1))).strftime('%Y-%m-%d')

    supabase.table("payments").insert({
        'invoice_number': get_next_invoice(),
        'member_id':      int(f['member_id']),
        'plan_id':        int(f['plan_id']),
        'amount':         amount,
        'payment_mode':   f['payment_mode'],
        'payment_status': 'completed',
        'payment_date':   f['payment_date'],
        'remarks':        sanitize(f.get('notes', '')),
    }).execute()
    supabase.table("members").update({'expiry_date': valid_to, 'status': 'active'}).eq("id", f['member_id']).execute()
    flash('Payment added!', 'success')
    return redirect(url_for('payments'))

@app.route('/admin/payments/delete/<int:payment_id>', methods=['POST'])
@admin_required
def delete_payment(payment_id):
    supabase.table("payments").delete().eq("id", payment_id).execute()
    flash('Payment deleted.', 'success')
    return redirect(url_for('payments'))

@app.route('/admin/payments/edit/<int:payment_id>', methods=['GET', 'POST'])
@admin_required
def edit_payment(payment_id):
    if request.method == 'POST':
        f = request.form
        supabase.table("payments").update({
            'payment_mode':   f['payment_mode'],
            'payment_status': f.get('payment_status', 'completed'),
            'payment_date':   f['payment_date'],
            'amount':         float(f['amount']),
            'remarks':        sanitize(f.get('remarks', '')),
        }).eq("id", payment_id).execute()
        flash('Payment updated!', 'success')
        return redirect(url_for('payments'))

    res = supabase.table("payments").select("*, members(full_name, member_id), membership_plans(plan_name)").eq("id", payment_id).execute()
    if not res.data:
        flash('Payment not found.', 'danger')
        return redirect(url_for('payments'))
    payment = res.data[0]
    payment['member_name'] = (payment.get('members') or {}).get('full_name', 'N/A')
    payment['plan_name']   = (payment.get('membership_plans') or {}).get('plan_name', 'N/A')
    payment['net_amount']  = payment.get('amount', 0)
    payment['discount']    = payment.get('discount', 0) or 0
    return render_template('edit_payment.html', payment=payment, settings=get_gym_settings())

@app.route('/admin/payments/invoice/<int:payment_id>')
@login_required
def view_invoice(payment_id):
    res = supabase.table("payments").select("*, members(*), membership_plans(*)").eq("id", payment_id).execute()
    if not res.data:
        flash('Invoice not found.', 'danger')
        return redirect(url_for('payments'))
    payment = res.data[0]
    member  = payment.get('members') or {}
    plan    = payment.get('membership_plans') or None

    trainer = None
    if member.get('trainer_id'):
        tr = supabase.table("trainers").select("*").eq("id", member['trainer_id']).execute()
        trainer = tr.data[0] if tr.data else None

    payment['net_amount']  = payment.get('net_amount') or payment.get('amount', 0)
    payment['discount']    = payment.get('discount', 0) or 0
    payment['valid_from']  = payment.get('valid_from') or payment.get('payment_date', '')
    if not payment.get('valid_to') and plan and plan.get('duration_months'):
        try:
            vf = datetime.strptime(str(payment['valid_from'])[:10], '%Y-%m-%d').date()
            payment['valid_to'] = (vf + timedelta(days=30 * plan['duration_months'])).strftime('%Y-%m-%d')
        except:
            payment['valid_to'] = ''
    else:
        payment['valid_to'] = payment.get('valid_to') or ''
    if not payment.get('invoice_number'):
        payment['invoice_number'] = f"INV-{payment['id']}"

    return render_template('invoice.html', payment=payment, member=member,
                           plan=plan, trainer=trainer, settings=get_gym_settings())

# ════════════════════════════════════════
#   ADMIN — COMPLAINTS
# ════════════════════════════════════════
@app.route('/admin/complaints')
@admin_required
def admin_complaints():
    data = supabase.table("complaints").select("*, members(full_name, member_id)").order("created_at", desc=True).execute().data or []
    for c in data:
        c['member_name'] = (c.get('members') or {}).get('full_name', 'N/A')
        c['member_code'] = (c.get('members') or {}).get('member_id', '')

    open_count     = sum(1 for c in data if c.get('status') == 'open')
    resolved_count = sum(1 for c in data if c.get('status') == 'resolved')
    open_replies   = sum(1 for c in data if not c.get('admin_reply'))

    return render_template('admin_complaints.html', complaints=data,
        open_count=open_count, resolved_count=resolved_count,
        open_replies=open_replies, settings=get_gym_settings())

@app.route('/admin/complaints/reply/<int:complaint_id>', methods=['POST'])
@admin_required
def reply_complaint(complaint_id):
    reply  = sanitize(request.form.get('reply', ''))
    status = request.form.get('status', 'resolved')
    supabase.table("complaints").update({'admin_reply': reply, 'status': status}).eq("id", complaint_id).execute()
    logger.info("Complaint replied: id=%s status=%s by admin %s", complaint_id, status, session.get('username'))
    flash('Reply sent!', 'success')
    return redirect(url_for('admin_complaints'))

# ════════════════════════════════════════
#   ADMIN — MESSAGES
# ════════════════════════════════════════
@app.route('/admin/messages')
@admin_required
def admin_messages():
    data = supabase.table("messages").select("*, members(full_name, member_id)").order("created_at", desc=True).execute().data or []
    for m in data:
        m['member_name'] = (m.get('members') or {}).get('full_name', 'N/A')
        m['member_code'] = (m.get('members') or {}).get('member_id', '')

    unreplied   = sum(1 for m in data if not m.get('reply'))
    all_members = supabase.table("members").select("id, full_name, member_id").execute().data or []

    return render_template('admin_messages.html', messages=data,
        unreplied=unreplied, members=all_members, settings=get_gym_settings())

@app.route('/admin/messages/reply/<int:msg_id>', methods=['POST'])
@admin_required
def reply_message(msg_id):
    supabase.table("messages").update({
        'reply':  sanitize(request.form.get('reply', '')),
        'status': 'replied',
    }).eq("id", msg_id).execute()
    flash('Reply sent!', 'success')
    return redirect(url_for('admin_messages'))

@app.route('/admin/messages/send', methods=['POST'])
@admin_required
def send_personal_message():
    supabase.table("messages").insert({
        'member_id': int(request.form['member_id']),
        'subject':   sanitize(request.form['subject']),
        'message':   sanitize(request.form['message']),
        'to_type':   'gym',
        'status':    'admin_sent',
    }).execute()
    flash('Message sent!', 'success')
    return redirect(url_for('admin_messages'))

# ════════════════════════════════════════
#   ADMIN — ANNOUNCEMENTS
# ════════════════════════════════════════
@app.route('/admin/announcements')
@admin_required
def announcements():
    data = supabase.table("announcements").select("*").order("created_at", desc=True).execute().data or []
    reads_raw = supabase.table("announcement_reads").select("announcement_id, member_id").execute().data or []
    announcement_reads = {}
    for r in reads_raw:
        aid = r['announcement_id']
        if aid not in announcement_reads:
            announcement_reads[aid] = []
        announcement_reads[aid].append(r['member_id'])
    return render_template('admin_announcements.html', announcements=data,
                           announcement_reads=announcement_reads, settings=get_gym_settings())

@app.route('/admin/announcements/add', methods=['POST'])
@admin_required
def add_announcement():
    supabase.table("announcements").insert({
        'title':      sanitize(request.form['title']),
        'message':    sanitize(request.form['message']),
        'priority':   request.form.get('priority', 'info'),
        'created_by': session['user_id'],
        'is_active':  True,
    }).execute()
    flash('Announcement added!', 'success')
    return redirect(url_for('announcements'))

@app.route('/admin/announcements/delete/<int:announcement_id>', methods=['POST'])
@admin_required
def delete_announcement(announcement_id):
    supabase.table("announcements").delete().eq("id", announcement_id).execute()
    flash('Announcement deleted.', 'success')
    return redirect(url_for('announcements'))

# ════════════════════════════════════════
#   ADMIN — REPORTS & SETTINGS
# ════════════════════════════════════════
@app.route('/admin/check-expiring', methods=['POST'])
@admin_required
def check_expiring():
    members = supabase.table("members").select("*").eq("status", "active").execute().data or []
    today   = date.today()
    for m in members:
        try:
            exp      = datetime.strptime(str(m['expiry_date'])[:10], '%Y-%m-%d').date()
            if (exp - today).days < 0:
                supabase.table("members").update({'status': 'expired'}).eq("id", m['id']).execute()
        except:
            pass
    flash('Membership expiry check complete.', 'info')
    return redirect(url_for('dashboard'))

@app.route('/admin/reports')
@admin_required
def reports():
    members  = supabase.table("members").select("*").execute().data or []
    payments = supabase.table("payments").select("*").execute().data or []

    active_members   = sum(1 for m in members if m.get('status') == 'active')
    expired_members  = sum(1 for m in members if m.get('status') == 'expired')
    total_revenue    = sum(float(p.get('amount', 0)) for p in payments if p.get('payment_status') == 'completed')
    pending_payments = sum(1 for p in payments if p.get('payment_status') == 'pending')

    month_keys = []
    for i in range(5, -1, -1):
        d = date.today().replace(day=1) - timedelta(days=i * 28)
        month_keys.append(d.strftime('%b %Y'))

    monthly_rev = {k: 0 for k in month_keys}
    for p in payments:
        try:
            key = datetime.strptime(str(p['payment_date'])[:10], '%Y-%m-%d').strftime('%b %Y')
            if key in monthly_rev:
                monthly_rev[key] += float(p.get('amount', 0))
        except: pass

    monthly_growth = {k: 0 for k in month_keys}
    for m in members:
        try:
            key = datetime.strptime(str(m['join_date'])[:10], '%Y-%m-%d').strftime('%b %Y')
            if key in monthly_growth:
                monthly_growth[key] += 1
        except: pass

    mode_data = {'Cash': 0, 'UPI': 0, 'Card': 0, 'Online': 0}
    for p in payments:
        mode = p.get('payment_mode', 'Other')
        if mode in mode_data:
            mode_data[mode] += float(p.get('amount', 0))

    last_month       = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
    last_month_count = sum(1 for m in members if str(m.get('join_date', ''))[:7] == last_month)

    for p in payments:
        p['net_amount'] = p.get('amount', 0)
        if not p.get('invoice_number'):
            p['invoice_number'] = f"INV-{p['id']}"

    return render_template('reports.html',
        total_members=len(members), active_members=active_members,
        expired_members=expired_members, total_revenue=total_revenue,
        pending_payments=pending_payments, last_month_count=last_month_count,
        payments=payments,
        monthly_labels=list(monthly_rev.keys()),
        monthly_values=list(monthly_rev.values()),
        growth_labels=list(monthly_growth.keys()),
        growth_values=list(monthly_growth.values()),
        mode_labels=list(mode_data.keys()),
        mode_values=list(mode_data.values()),
        settings=get_gym_settings())

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    if request.method == 'POST':
        f = request.form
        logo_filename = None
        if 'gym_logo' in request.files:
            logo = request.files['gym_logo']
            if logo and logo.filename and allowed_file(logo.filename):
                logo_filename = f"logo_{uuid.uuid4().hex[:8]}.{logo.filename.rsplit('.',1)[1].lower()}"
                logo.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))

        data = {
            'gym_name':    sanitize(f['gym_name']),
            'gym_address': sanitize(f.get('gym_address', '')),
            'gym_phone':   sanitize(f.get('gym_phone', ''), 20),
            'gym_email':   sanitize(f.get('gym_email', ''), 200),
            'gym_website': sanitize(f.get('gym_website', ''), 200),
            'theme':       f.get('theme', 'dark'),
            'currency':    f.get('currency', '₹'),
        }
        if logo_filename:
            data['gym_logo'] = logo_filename

        existing = supabase.table("gym_settings").select("id").execute().data
        if existing:
            supabase.table("gym_settings").update(data).eq("id", existing[0]['id']).execute()
        else:
            supabase.table("gym_settings").insert(data).execute()

        flash('Settings updated!', 'success')
        return redirect(url_for('settings'))

    return render_template('settings.html', settings=get_gym_settings())

# ════════════════════════════════════════
#   MEMBER PORTAL
# ════════════════════════════════════════
@app.route('/member/dashboard')
@member_login_required
def member_dashboard():
    uid = session['user_id']
    res = supabase.table("members").select("*").eq("id", uid).execute()
    member = res.data[0] if res.data else {}

    plan = None
    if member.get('membership_plan_id'):
        pr = supabase.table("membership_plans").select("*").eq("id", member['membership_plan_id']).execute()
        plan = pr.data[0] if pr.data else None

    trainer = None
    if member.get('trainer_id'):
        tr = supabase.table("trainers").select("*").eq("id", member['trainer_id']).execute()
        trainer = tr.data[0] if tr.data else None

    member['plan_name']         = plan.get('plan_name', 'N/A') if plan else 'N/A'
    member['trainer_name']      = trainer.get('full_name', 'N/A') if trainer else 'N/A'
    member['membership_status'] = member.get('status', 'active')

    days_left_num = 0
    try:
        exp = datetime.strptime(str(member['expiry_date'])[:10], '%Y-%m-%d').date()
        days_left_num = (exp - date.today()).days
    except:
        pass

    payments_raw = supabase.table("payments").select("*").eq("member_id", uid).order("payment_date", desc=True).limit(5).execute().data or []
    for p in payments_raw:
        p['net_amount'] = p.get('amount', 0)
        if not p.get('invoice_number'):
            p['invoice_number'] = f"INV-{p['id']}"

    total_payments = len(supabase.table("payments").select("id").eq("member_id", uid).execute().data or [])

    att_data = supabase.table("attendance").select("attendance_date").eq("member_id", uid).execute().data or []
    attendance_dates = [str(a.get('attendance_date',''))[:10] for a in att_data]
    this_month = date.today().strftime('%Y-%m')
    month_attendance = sum(1 for d in attendance_dates if d[:7] == this_month)

    complaints = supabase.table("complaints").select("admin_reply, status").eq("member_id", uid).execute().data or []
    open_replies = sum(1 for c in complaints if c.get('admin_reply') and c.get('status') != 'closed')

    announcements = supabase.table("announcements").select("*").eq("is_active", True).order("created_at", desc=True).limit(5).execute().data or []

    return render_template('member_dashboard.html', member=member,
        plan=plan, trainer=trainer, days_left_num=days_left_num,
        payments=payments_raw, attendance=attendance_dates,
        month_attendance=month_attendance, total_payments=total_payments,
        open_replies=open_replies,
        announcements=announcements, settings=get_gym_settings())

@app.route('/member/profile', methods=['GET', 'POST'])
@member_login_required
def member_profile():
    if request.method == 'POST':
        f      = request.form
        action = f.get('action', 'update_info')

        if action == 'change_password':
            # Verify current password first
            res = supabase.table("members").select("password_hash").eq("id", session['user_id']).execute()
            if res.data:
                stored = res.data[0].get('password_hash', '')
                if not check_password_hash(stored, f.get('current_password', '')):
                    flash('Current password is incorrect.', 'danger')
                    return redirect(url_for('member_profile'))
            new_pw = f.get('new_password', '').strip()
            if len(new_pw) < 4:
                flash('New password must be at least 4 characters.', 'danger')
                return redirect(url_for('member_profile'))
            supabase.table("members").update({'password_hash': generate_password_hash(new_pw)}).eq("id", session['user_id']).execute()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('member_profile'))

        # update_info action
        data = {
            'phone':             sanitize(f.get('phone', ''), 20),
            'address':           sanitize(f.get('address', '')),
            'emergency_contact': sanitize(f.get('emergency_contact', ''), 100),
        }
        if f.get('email'):
            data['email'] = sanitize(f.get('email', ''), 200)
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and photo.filename and allowed_file(photo.filename):
                fname = f"member_{uuid.uuid4().hex[:8]}.{photo.filename.rsplit('.',1)[1].lower()}"
                photo.save(os.path.join(app.config['UPLOAD_FOLDER'], 'members', fname))
                data['photo'] = fname
        supabase.table("members").update(data).eq("id", session['user_id']).execute()
        flash('Profile updated!', 'success')
        return redirect(url_for('member_profile'))

    res = supabase.table("members").select("*").eq("id", session['user_id']).execute()
    member = res.data[0] if res.data else {}
    plan = None
    if member.get('membership_plan_id'):
        pr = supabase.table("membership_plans").select("*").eq("id", member['membership_plan_id']).execute()
        plan = pr.data[0] if pr.data else None
    trainer = None
    if member.get('trainer_id'):
        tr = supabase.table("trainers").select("*").eq("id", member['trainer_id']).execute()
        trainer = tr.data[0] if tr.data else None
    member['membership_status'] = member.get('status', 'active')
    return render_template('member_profile.html', member=member, plan=plan, trainer=trainer, settings=get_gym_settings())

@app.route('/member/attendance')
@member_login_required
def member_attendance():
    uid  = session['user_id']
    data = supabase.table("attendance").select("attendance_date").eq("member_id", uid).order("attendance_date", desc=True).execute().data or []
    res  = supabase.table("members").select("*").eq("id", uid).execute()
    member = res.data[0] if res.data else {}

    total_visits = len(data)
    this_month   = date.today().strftime('%Y-%m')
    last_month   = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m')
    month_count      = sum(1 for a in data if str(a.get('attendance_date',''))[:7] == this_month)
    last_month_count = sum(1 for a in data if str(a.get('attendance_date',''))[:7] == last_month)

    streak = 0
    today  = date.today()
    dates  = sorted([datetime.strptime(str(a['attendance_date'])[:10], '%Y-%m-%d').date() for a in data], reverse=True)
    for i, d in enumerate(dates):
        if d == today - timedelta(days=i):
            streak += 1
        else:
            break

    month_attendance = {}
    for a in data:
        key = str(a.get('attendance_date',''))[:7]
        month_attendance[key] = month_attendance.get(key, 0) + 1

    calendar_data = {}
    for a in data:
        date_str  = str(a.get('attendance_date',''))[:10]
        month_key = date_str[:7]
        if month_key not in calendar_data:
            calendar_data[month_key] = []
        calendar_data[month_key].append(date_str)
    calendar_data = dict(sorted(calendar_data.items(), reverse=True))

    attendance_dates = [str(a.get('attendance_date',''))[:10] for a in data]

    return render_template('member_attendance.html', member=member,
        attendance=attendance_dates,
        total_visits=total_visits, month_count=month_count,
        last_month_count=last_month_count, streak=streak,
        month_attendance=month_attendance, calendar_data=calendar_data,
        settings=get_gym_settings())

@app.route('/member/invoices')
@member_login_required
def member_invoices():
    data = supabase.table("payments").select("*, membership_plans(*)").eq("member_id", session['user_id']).order("payment_date", desc=True).execute().data or []
    for p in data:
        plan_obj = p.get('membership_plans') or {}
        p['plan_name']  = plan_obj.get('plan_name', 'N/A')
        p['net_amount'] = p.get('amount', 0)
        p['discount']   = p.get('discount', 0) or 0
        p['valid_from'] = p.get('valid_from') or p.get('payment_date', '')
        if not p.get('valid_to') and plan_obj.get('duration_months'):
            try:
                vf = datetime.strptime(str(p['valid_from'])[:10], '%Y-%m-%d').date()
                p['valid_to'] = (vf + timedelta(days=30 * plan_obj['duration_months'])).strftime('%Y-%m-%d')
            except:
                p['valid_to'] = ''
        else:
            p['valid_to'] = p.get('valid_to') or ''
        if not p.get('invoice_number'):
            p['invoice_number'] = f"INV-{p['id']}"
    res    = supabase.table("members").select("*").eq("id", session['user_id']).execute()
    member = res.data[0] if res.data else {}
    return render_template('member_invoices.html', member=member, payments=data, settings=get_gym_settings())

@app.route('/member/complaints', methods=['GET', 'POST'])
@member_login_required
def member_complaints():
    if request.method == 'POST':
        subject = sanitize(request.form.get('subject', ''))
        message = sanitize(request.form.get('message', ''))
        if not subject or not message:
            flash('Subject and message are required.', 'danger')
            return redirect(url_for('member_complaints'))
        supabase.table("complaints").insert({
            'member_id': session['user_id'],
            'subject':   subject,
            'message':   message,
            'category':  request.form.get('category', ''),
            'status':    'open',
        }).execute()
        flash('Complaint submitted!', 'success')
        return redirect(url_for('member_complaints'))

    data = supabase.table("complaints").select("*").eq("member_id", session['user_id']).order("created_at", desc=True).execute().data or []

    resolved_ids = [c['id'] for c in data if c.get('status') == 'resolved' and c.get('admin_reply')]
    if resolved_ids:
        for cid in resolved_ids:
            supabase.table("complaints").update({'status': 'closed'}).eq("id", cid).execute()
        data = supabase.table("complaints").select("*").eq("member_id", session['user_id']).order("created_at", desc=True).execute().data or []

    res    = supabase.table("members").select("*").eq("id", session['user_id']).execute()
    member = res.data[0] if res.data else {}
    return render_template('member_complaints.html', member=member, complaints=data, settings=get_gym_settings())

@app.route('/member/contact', methods=['GET', 'POST'])
@member_login_required
def member_contact():
    if request.method == 'POST':
        subject = sanitize(request.form.get('subject', ''))
        message = sanitize(request.form.get('message', ''))
        if not subject or not message:
            flash('Subject and message are required.', 'danger')
            return redirect(url_for('member_contact'))
        supabase.table("messages").insert({
            'member_id': session['user_id'],
            'subject':   subject,
            'message':   message,
            'to_type':   request.form.get('to', 'gym'),
            'status':    'sent',
        }).execute()
        flash('Message sent!', 'success')
        return redirect(url_for('member_contact'))

    data   = supabase.table("messages").select("*").eq("member_id", session['user_id']).order("created_at", desc=True).execute().data or []
    res    = supabase.table("members").select("*").eq("id", session['user_id']).execute()
    member = res.data[0] if res.data else {}
    trainer = None
    if member.get('trainer_id'):
        tr = supabase.table("trainers").select("*").eq("id", member['trainer_id']).execute()
        trainer = tr.data[0] if tr.data else None
    gym_settings = get_gym_settings()
    return render_template('member_contact.html', member=member, messages=data,
                           trainer=trainer, gym_settings=gym_settings, settings=gym_settings)

@app.route('/member/announcements')
@member_login_required
def member_announcements():
    data = supabase.table("announcements").select("*").eq("is_active", True).order("created_at", desc=True).execute().data or []
    reads = supabase.table("announcement_reads").select("announcement_id").eq("member_id", session['user_id']).execute().data or []
    read_ids = {r['announcement_id'] for r in reads}
    for a in data:
        a['is_read'] = a['id'] in read_ids
    unread_count = sum(1 for a in data if not a['is_read'])
    res    = supabase.table("members").select("*").eq("id", session['user_id']).execute()
    member = res.data[0] if res.data else {}
    return render_template('member_announcements.html', member=member, announcements=data,
                           unread_count=unread_count, settings=get_gym_settings())

@app.route('/member/announcements/mark-read/<int:announcement_id>', methods=['POST'])
@member_login_required
def mark_announcement_read(announcement_id):
    existing = supabase.table("announcement_reads").select("id").eq("announcement_id", announcement_id).eq("member_id", session['user_id']).execute().data
    if not existing:
        supabase.table("announcement_reads").insert({'announcement_id': announcement_id, 'member_id': session['user_id']}).execute()
    return redirect(url_for('member_announcements'))

# ════════════════════════════════════════
#   API — rate limited + protected
# ════════════════════════════════════════
@app.route('/api/trainers')
@api_protected
@limiter.limit("100/minute")
def api_trainers():
    data = supabase.table("trainers").select("*").execute().data or []
    return jsonify(data)

@app.route('/api/members')
@api_protected
@limiter.limit("100/minute")
def api_members():
    if session.get('role') != 'admin':
        return jsonify({'error': 'Forbidden'}), 403
    data = supabase.table("members").select("*").execute().data or []
    return jsonify(data)

@app.route('/api/plans')
@limiter.limit("100/minute")
def api_plans():
    data = supabase.table("membership_plans").select("*").execute().data or []
    return jsonify(data)

@app.route('/api/member/<int:member_id>')
@api_protected
@limiter.limit("100/minute")
def api_member(member_id):
    # Members can only access their own data
    if session.get('role') == 'member' and session.get('user_id') != member_id:
        return jsonify({'error': 'Forbidden'}), 403
    res = supabase.table("members").select("*").eq("id", member_id).execute()
    return jsonify(res.data[0]) if res.data else (jsonify({'error': 'Not found'}), 404)

@app.route('/api/plan/<int:plan_id>')
@api_protected
@limiter.limit("100/minute")
def api_plan(plan_id):
    res = supabase.table("membership_plans").select("*").eq("id", plan_id).execute()
    return jsonify(res.data[0]) if res.data else (jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    app.run(debug=True)
