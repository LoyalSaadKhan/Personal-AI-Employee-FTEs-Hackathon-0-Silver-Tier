---
name: scheduled-operations
description: |
  Scheduled operations via cron (Linux/Mac) or Task Scheduler (Windows).
  Enables automated daily briefings, hourly checks, and recurring tasks.
---

# Scheduled Operations - Silver Tier

## Overview

Scheduled operations enable the AI Employee to run automatically at specified times:
- Daily CEO Briefings
- Hourly pending item checks
- Weekly business audits
- Social media posting
- Inbox cleanup

---

## Scheduling Options

### Option 1: Windows Task Scheduler

Best for: Windows users, desktop deployment

### Option 2: Linux/Mac cron

Best for: Linux/Mac users, server deployment

### Option 3: Python Scheduler (Cross-platform)

Best for: Development/testing, simple deployments

---

## Windows Task Scheduler Setup

### Daily Briefing (8:00 AM)

```powershell
# Create scheduled task for daily briefing
$action = New-ScheduledTaskAction `
  -Execute "python" `
  -Argument "scripts/orchestrator.py C:\Users\Jawaria Noor\Desktop\Personal-AI-Employee-FTEs\Personal-AI-Employee-FTEs\AI_Employee_Vault --daily-briefing" `
  -WorkingDirectory "C:\Users\Jawaria Noor\Desktop\Personal-AI-Employee-FTEs\Personal-AI-Employee-FTEs"

$trigger = New-ScheduledTaskTrigger `
  -Daily `
  -At 8:00AM `
  -DaysInterval 1

$principal = New-ScheduledTaskPrincipal `
  -UserId "SYSTEM" `
  -LogonType ServiceAccount `
  -RunLevel Highest

$settings = New-ScheduledTaskSettingsSet `
  -AllowStartIfOnBatteries `
  -DontStopIfGoingOnBatteries `
  -StartWhenAvailable `
  -RunOnlyIfNetworkAvailable

Register-ScheduledTask `
  -TaskName "AI_Employee_Daily_Briefing" `
  -Action $action `
  -Trigger $trigger `
  -Principal $principal `
  -Settings $settings `
  -Description "Generate daily CEO briefing every morning at 8 AM"
```

### Hourly Check

```powershell
# Create scheduled task for hourly checks
$action = New-ScheduledTaskAction `
  -Execute "python" `
  -Argument "scripts/orchestrator.py C:\Users\Jawaria Noor\Desktop\Personal-AI-Employee-FTEs\Personal-AI-Employee-FTEs\AI_Employee_Vault" `
  -WorkingDirectory "C:\Users\Jawaria Noor\Desktop\Personal-AI-Employee-FTEs\Personal-AI-Employee-FTEs"

$trigger = New-ScheduledTaskTrigger `
  -Once `
  -At (Get-Date) `
  -RepetitionInterval (New-TimeSpan -Hours 1) `
  -RepetitionDuration ([TimeSpan]::MaxValue)

Register-ScheduledTask `
  -TaskName "AI_Employee_Hourly_Check" `
  -Action $action `
  -Trigger $trigger `
  -Description "Check for pending items every hour"
```

### LinkedIn Post (9:00 AM Daily)

```powershell
# Create scheduled task for LinkedIn posting
$action = New-ScheduledTaskAction `
  -Execute "python" `
  -Argument "scripts/linkedin_poster.py C:\Users\Jawaria Noor\Desktop\Personal-AI-Employee-FTEs\Personal-AI-Employee-FTEs\AI_Employee_Vault --publish" `
  -WorkingDirectory "C:\Users\Jawaria Noor\Desktop\Personal-AI-Employee-FTEs\Personal-AI-Employee-FTEs"

$trigger = New-ScheduledTaskTrigger `
  -Daily `
  -At 9:00AM

Register-ScheduledTask `
  -TaskName "AI_Employee_LinkedIn_Post" `
  -Action $action `
  -Trigger $trigger `
  -Description "Publish LinkedIn post every weekday at 9 AM"
```

### Manage Scheduled Tasks

```powershell
# View all AI Employee tasks
Get-ScheduledTask -TaskName "AI_Employee_*"

# View task history
Get-ScheduledTaskInfo -TaskName "AI_Employee_Daily_Briefing"

# Export task configuration
Export-ScheduledTask -TaskName "AI_Employee_Daily_Briefing" | Out-File "AI_Employee_Daily_Briefing.xml"

# Import task from XML
Register-ScheduledTask -Xml (Get-Content "AI_Employee_Daily_Briefing.xml" | Out-String)

# Disable task
Disable-ScheduledTask -TaskName "AI_Employee_Hourly_Check"

# Enable task
Enable-ScheduledTask -TaskName "AI_Employee_Hourly_Check"

# Delete task
Unregister-ScheduledTask -TaskName "AI_Employee_Daily_Briefing" -Confirm:$false
```

---

## Linux/Mac cron Setup

### Edit Crontab

```bash
# Open crontab editor
crontab -e

# Or for specific user
crontab -u username -e
```

### Cron Configuration

```bash
# Environment variables
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
PYTHONPATH=/path/to/venv/lib/python3.13/site-packages

# AI Employee Scheduled Tasks

# Daily briefing at 8:00 AM
0 8 * * * cd /path/to/Personal-AI-Employee-FTEs && ./venv/bin/python scripts/orchestrator.py ./AI_Employee_Vault --daily-briefing >> /tmp/ai_employee_briefing.log 2>&1

# Hourly check (every hour at :00)
0 * * * * cd /path/to/Personal-AI-Employee-FTEs && ./venv/bin/python scripts/orchestrator.py ./AI_Employee_Vault >> /tmp/ai_employee_hourly.log 2>&1

# LinkedIn post at 9:00 AM (weekdays only)
0 9 * * 1-5 cd /path/to/Personal-AI-Employee-FTEs && ./venv/bin/python scripts/linkedin_poster.py ./AI_Employee_Vault --publish >> /tmp/ai_employee_linkedin.log 2>&1

# Weekly audit every Monday at 7:00 AM
0 7 * * 1 cd /path/to/Personal-AI-Employee-FTEs && ./venv/bin/python scripts/orchestrator.py ./AI_Employee_Vault --weekly-audit >> /tmp/ai_employee_weekly.log 2>&1

# Daily cleanup at 6:00 PM
0 18 * * * cd /path/to/Personal-AI-Employee-FTEs && ./venv/bin/python scripts/cleanup.py ./AI_Employee_Vault >> /tmp/ai_employee_cleanup.log 2>&1
```

### Cron Management Commands

```bash
# View current crontab
crontab -l

# Backup crontab
crontab -l > crontab_backup.txt

# Restore crontab
crontab crontab_backup.txt

# Remove all cron jobs
crontab -r

# View cron logs (Linux)
grep CRON /var/log/syslog

# View cron logs (Mac)
log show --predicate 'process == "cron"' --last 1h
```

---

## Python Scheduler (Cross-platform)

For development or simple deployments:

```python
#!/usr/bin/env python3
"""
Simple Python scheduler for AI Employee tasks.
Alternative to cron/Task Scheduler for development.

Usage:
    python scheduler.py /path/to/vault
"""

import sys
import time
import logging
import schedule
from pathlib import Path
from datetime import datetime

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent / 'scripts'))

from orchestrator import Orchestrator

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('Scheduler')


class AIScheduler:
    """Scheduler for AI Employee tasks."""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.orchestrator = Orchestrator(str(vault_path), check_interval=60)
    
    def run_daily_briefing(self):
        """Generate daily CEO briefing."""
        logger.info('Running daily briefing...')
        try:
            # Generate briefing
            self.orchestrator.run_cycle()
            logger.info('Daily briefing complete')
        except Exception as e:
            logger.error(f'Daily briefing failed: {e}')
    
    def run_hourly_check(self):
        """Check for pending items."""
        logger.info('Running hourly check...')
        try:
            self.orchestrator.run_cycle()
            logger.info('Hourly check complete')
        except Exception as e:
            logger.error(f'Hourly check failed: {e}')
    
    def run_cleanup(self):
        """Clean up old files."""
        logger.info('Running cleanup...')
        # Cleanup logic here
        logger.info('Cleanup complete')
    
    def start(self):
        """Start the scheduler."""
        logger.info('Starting AI Employee Scheduler')
        
        # Schedule tasks
        schedule.every().day.at('08:00').do(self.run_daily_briefing)
        schedule.every().hour.at(':00').do(self.run_hourly_check)
        schedule.every().day.at('18:00').do(self.run_cleanup)
        
        logger.info('Scheduled tasks:')
        logger.info('  - Daily briefing: 08:00')
        logger.info('  - Hourly check: Every hour at :00')
        logger.info('  - Cleanup: 18:00')
        
        # Run scheduler loop
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute


def main():
    if len(sys.argv) < 2:
        print('Usage: python scheduler.py <vault_path>')
        sys.exit(1)
    
    vault_path = Path(sys.argv[1]).resolve()
    
    if not vault_path.exists():
        print(f'Error: Vault not found: {vault_path}')
        sys.exit(1)
    
    scheduler = AIScheduler(str(vault_path))
    
    try:
        scheduler.start()
    except KeyboardInterrupt:
        logger.info('Scheduler stopped by user')


if __name__ == '__main__':
    main()
```

---

## Scheduled Task Types

### Daily Briefing

**When:** 8:00 AM daily
**Purpose:** Summarize yesterday's activities and prepare for today

**Output:**
```markdown
# Daily Briefing - 2026-03-20

## Yesterday's Summary
- Tasks completed: 12
- Emails processed: 8
- Approvals handled: 3

## Today's Priorities
- [ ] Follow up on pending approvals
- [ ] Process overnight emails
- [ ] Post LinkedIn update

## Revenue Update
- MTD: $4,500
- Target: $10,000
- Progress: 45%
```

### Hourly Check

**When:** Every hour at :00
**Purpose:** Process pending items, check for new tasks

**Actions:**
- Check /Needs_Action/ for new items
- Trigger Qwen Code if items found
- Update Dashboard
- Log activity

### Weekly Audit

**When:** Monday 7:00 AM
**Purpose:** Comprehensive business review

**Output:** CEO Briefing in /Briefings/

### Social Media Post

**When:** 9:00 AM weekdays
**Purpose:** Consistent social media presence

**Actions:**
- Generate post (8:00 AM)
- Publish post (9:00 AM)
- Log engagement

### Daily Cleanup

**When:** 6:00 PM daily
**Purpose:** Maintain vault hygiene

**Actions:**
- Archive old completed tasks
- Clean up temp files
- Rotate logs

---

## Monitoring Scheduled Tasks

### Check Task Status

```powershell
# Windows: Check last run result
Get-ScheduledTaskInfo -TaskName "AI_Employee_Daily_Briefing" | 
  Select-Object TaskName, LastRunTime, LastTaskResult
```

```bash
# Linux: Check cron logs
grep "AI_Employee" /var/log/syslog | tail -20
```

### Health Check Script

```python
#!/usr/bin/env python3
"""Health check for scheduled tasks."""

import subprocess
import sys
from pathlib import Path
from datetime import datetime, timedelta

def check_scheduled_tasks():
    """Check if scheduled tasks are running."""
    issues = []
    
    # Check Windows Task Scheduler
    if sys.platform == 'win32':
        result = subprocess.run(
            ['powershell', '-Command', 
             'Get-ScheduledTask -TaskName "AI_Employee_*" | Get-ScheduledTaskInfo'],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            issues.append('Failed to query scheduled tasks')
    
    # Check last orchestrator run
    log_file = Path('AI_Employee_Vault/Logs/2026-03-20.log')
    if log_file.exists():
        content = log_file.read_text()
        if 'Orchestrator initialized' not in content:
            issues.append('No orchestrator activity today')
    
    return issues

if __name__ == '__main__':
    issues = check_scheduled_tasks()
    if issues:
        print('Health check FAILED:')
        for issue in issues:
            print(f'  - {issue}')
        sys.exit(1)
    else:
        print('Health check PASSED')
        sys.exit(0)
```

---

## Troubleshooting

### Task Not Running

**Windows:**
```powershell
# Check task status
Get-ScheduledTask -TaskName "AI_Employee_Daily_Briefing"

# Check last run result
Get-ScheduledTaskInfo -TaskName "AI_Employee_Daily_Briefing"

# Run task manually to test
Start-ScheduledTask -TaskName "AI_Employee_Daily_Briefing"

# Check task history
Get-WinEvent -FilterHashtable @{
    LogName='Microsoft-Windows-TaskScheduler/Operational'
    Id=100,102,110,111,119,120,129,134,135,140,141
} | Where-Object {$_.Message -like '*AI_Employee*'} | Select-Object -First 20
```

**Linux:**
```bash
# Check cron service status
systemctl status cron

# Check cron logs
grep CRON /var/log/syslog | tail -50

# Test cron command manually
cd /path/to/Personal-AI-Employee-FTEs && ./venv/bin/python scripts/orchestrator.py ./AI_Employee_Vault
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Task not running | Python not in PATH | Use absolute path to Python |
| Task fails silently | No output redirection | Add `>> log.txt 2>&1` |
| Permission denied | Running as wrong user | Run as logged-in user or SYSTEM |
| Network tasks fail | No network at startup | Add `-RunOnlyIfNetworkAvailable` |

---

## Best Practices

1. **Use absolute paths** - Avoid PATH issues
2. **Redirect output** - Capture logs for debugging
3. **Set working directory** - Use `-WorkingDirectory` or `cd`
4. **Test manually first** - Run command before scheduling
5. **Monitor regularly** - Check task history weekly
6. **Handle errors** - Log failures for debugging
7. **Rotate logs** - Prevent disk space issues

---

*Silver Tier Scheduled Operations v0.1*
