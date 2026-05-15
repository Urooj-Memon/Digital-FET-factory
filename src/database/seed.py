"""Seed the knowledge base with product documentation."""

import asyncio
import os
from pathlib import Path

import asyncpg


KNOWLEDGE_ENTRIES = [
    {
        "title": "Getting Started - Creating an Account",
        "content": "To create a TechFlow account: 1) Visit https://app.techflow.io/signup 2) Enter your email and create a password 3) Verify your email address 4) Set up your workspace name 5) Invite team members. The Free plan supports up to 5 users.",
        "category": "getting_started",
    },
    {
        "title": "Password Reset Process",
        "content": "To reset your password: 1) Go to https://app.techflow.io/forgot-password 2) Enter your registered email 3) Check your inbox for the reset link (valid for 24 hours) 4) Create a new password (minimum 8 characters, must include number and special character). If you don't receive the email, check spam folder or contact support.",
        "category": "account",
    },
    {
        "title": "Task Management - Creating and Managing Tasks",
        "content": "Creating Tasks: Click '+' button or press 'T' shortcut. Add title, description, assignee, due date, and priority. Kanban Board: Drag and drop tasks between columns (To Do, In Progress, Review, Done). Subtasks: Break tasks into smaller items by clicking 'Add subtask'. Labels: Color-coded labels for categorization (Bug, Feature, Enhancement).",
        "category": "features",
    },
    {
        "title": "Team Collaboration Features",
        "content": "Comments: Add comments on any task, use @mentions to notify team members. Real-time Chat: Built-in messaging with channels and DMs. File Sharing: Attach files up to 100MB per file, supports all common formats. Document Editor: Collaborative editing with version history.",
        "category": "features",
    },
    {
        "title": "Integrations - Slack",
        "content": "Slack integration provides two-way sync. Get task notifications in Slack and create tasks from Slack. Setup: Go to Settings > Integrations > Slack > Connect. Available on all paid plans.",
        "category": "integrations",
    },
    {
        "title": "Integrations - GitHub",
        "content": "GitHub integration lets you link pull requests to tasks. Task status auto-updates on merge. Setup: Settings > Integrations > GitHub > Authorize. You can link PRs by mentioning the task ID in your PR description.",
        "category": "integrations",
    },
    {
        "title": "Integrations - Jira",
        "content": "Import existing Jira projects into TechFlow. Bi-directional sync available on Business plan. Setup: Settings > Integrations > Jira > Connect. For large imports (1000+ tasks), the process may take several minutes.",
        "category": "integrations",
    },
    {
        "title": "API Documentation",
        "content": "Authentication: API key-based, generate keys in Settings > API. Rate Limits: Free=100 req/hr, Pro=1000 req/hr, Business=10000 req/hr. Key endpoints: GET /api/v1/tasks, POST /api/v1/tasks, PUT /api/v1/tasks/:id, DELETE /api/v1/tasks/:id, GET /api/v1/projects. Full docs at api.techflow.io.",
        "category": "api",
    },
    {
        "title": "Automation & Workflows",
        "content": "Triggers: When task status changes, when due date approaches, when assigned. Actions: Send notification, move to project, update priority, create subtask. Templates: Pre-built workflow templates for common processes. Access via Settings > Automation.",
        "category": "features",
    },
    {
        "title": "Time Tracking",
        "content": "Timer: Built-in timer on each task, click play/pause. Manual Entry: Add time entries manually with date and description. Reports: Weekly/monthly time reports by project, team, or individual. Export: Export time data as CSV or PDF from Reports > Time Tracking > Export.",
        "category": "features",
    },
    {
        "title": "Plans and Pricing",
        "content": "Free: $0/mo, up to 5 users, basic tasks, limited storage. Pro: $12/user/mo, up to 50 users, all features, 100GB storage. Business: $24/user/mo, unlimited users, advanced analytics, SSO, priority support. Enterprise: Custom pricing, unlimited users, custom integrations, dedicated support, SLA. For pricing inquiries, please contact our sales team.",
        "category": "billing",
    },
    {
        "title": "SSO/SAML Configuration",
        "content": "SSO/SAML is available on Business and Enterprise plans. Supports Okta, Azure AD, and Google Workspace. Setup: Settings > Security > SSO > Configure. You'll need your Identity Provider metadata URL and certificate. For Azure AD: Register TechFlow as an Enterprise Application in Azure Portal.",
        "category": "security",
    },
    {
        "title": "Data Export",
        "content": "Export all workspace data in JSON format: Settings > Data > Export. For time tracking exports: Reports > Time Tracking > Export (CSV or PDF). Individual project exports are also available from Project Settings > Export.",
        "category": "account",
    },
    {
        "title": "Troubleshooting - Login Issues",
        "content": "Can't log in: 1) Clear browser cache and cookies 2) Try incognito/private mode 3) Reset password via forgot-password page 4) Check if account is locked (5 failed attempts = 30-min lock) 5) Ensure you're using the correct workspace URL.",
        "category": "troubleshooting",
    },
    {
        "title": "Troubleshooting - File Upload Issues",
        "content": "File upload fails: 1) Check file size (max 100MB per file) 2) Verify file format is supported 3) Check storage quota (Settings > Storage) 4) Try a different browser 5) Disable browser extensions that might block uploads.",
        "category": "troubleshooting",
    },
    {
        "title": "Troubleshooting - Notification Issues",
        "content": "Notifications not working: 1) Check Settings > Notifications to ensure they're enabled 2) Check browser notification permissions 3) For mobile: ensure app notifications are enabled in phone settings 4) Check Do Not Disturb settings 5) For iOS: ensure Background App Refresh is enabled.",
        "category": "troubleshooting",
    },
    {
        "title": "Troubleshooting - Performance Issues",
        "content": "Slow performance: 1) Clear browser cache 2) Disable unused browser extensions 3) Try a different browser (Chrome recommended) 4) Check internet speed (minimum 5 Mbps) 5) Close unnecessary tabs 6) Check TechFlow status page for any ongoing issues.",
        "category": "troubleshooting",
    },
    {
        "title": "User Roles and Permissions",
        "content": "Owner: Full access, billing management, can delete workspace. Admin: Manage members, projects, and settings. Member: Create/edit tasks and projects assigned to them. Guest: View-only access to specific projects they're invited to. Manage roles in Settings > Members.",
        "category": "account",
    },
    {
        "title": "Account Deletion",
        "content": "To delete your account: Go to Settings > Account > Delete Account. This action is irreversible. All your data will be permanently deleted after 30 days. You can also contact support to request account deletion.",
        "category": "account",
    },
    {
        "title": "Mobile App",
        "content": "TechFlow mobile app is available for iOS 15+ and Android 12+. Download from App Store or Google Play. Features: View/edit tasks, receive notifications, chat, time tracking. Offline mode: View cached tasks offline, changes sync when back online.",
        "category": "features",
    },
    {
        "title": "Security and Compliance",
        "content": "Encryption: AES-256 at rest, TLS 1.3 in transit. Backups: Daily automated backups with 30-day retention. Compliance: SOC 2 Type II certified, GDPR compliant. Uptime SLA: 99.9% for Business, 99.99% for Enterprise. TechFlow is NOT currently HIPAA compliant.",
        "category": "security",
    },
    {
        "title": "Keyboard Shortcuts",
        "content": "T: Create new task, P: Create new project, /: Search, Ctrl+K: Command palette, Ctrl+Enter: Save and close, Esc: Cancel/close, Tab: Navigate fields, Shift+Tab: Previous field. Full list: Settings > Keyboard Shortcuts or press '?' anywhere.",
        "category": "features",
    },
    {
        "title": "Workspace vs Project Hierarchy",
        "content": "Workspace: Your top-level organization (company/team). One workspace per account. Project: A collection of related tasks within your workspace. You can have multiple projects. Task: Individual work items within a project. Can have subtasks.",
        "category": "getting_started",
    },
    {
        "title": "Bulk Task Import",
        "content": "Import tasks via CSV: Go to Project > Settings > Import > CSV. Required columns: title. Optional: description, assignee, due_date, priority, status, labels. Max 5000 tasks per import. Templates available for download on the import page.",
        "category": "features",
    },
    {
        "title": "Google Calendar Integration",
        "content": "Sync task due dates with Google Calendar. Setup: Settings > Integrations > Google Calendar > Connect. Two-way sync: Changes in either platform are reflected. Timezone handling: Uses your workspace timezone setting.",
        "category": "integrations",
    },
]


async def seed_knowledge_base():
    """Seed the knowledge base table with product documentation."""
    pool = await asyncpg.create_pool(
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", "5432")),
        database=os.getenv("POSTGRES_DB", "fte_db"),
        user=os.getenv("POSTGRES_USER", "fte_user"),
        password=os.getenv("POSTGRES_PASSWORD", "password"),
    )

    async with pool.acquire() as conn:
        # Clear existing entries
        await conn.execute("DELETE FROM knowledge_base")

        for entry in KNOWLEDGE_ENTRIES:
            await conn.execute(
                """INSERT INTO knowledge_base (title, content, category)
                   VALUES ($1, $2, $3)""",
                entry["title"],
                entry["content"],
                entry["category"],
            )

        count = await conn.fetchval("SELECT COUNT(*) FROM knowledge_base")
        print(f"Seeded {count} knowledge base entries.")

    await pool.close()


if __name__ == "__main__":
    asyncio.run(seed_knowledge_base())
