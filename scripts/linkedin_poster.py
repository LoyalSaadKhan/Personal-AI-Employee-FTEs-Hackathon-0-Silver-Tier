#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
LinkedIn Post Generator - Creates automated LinkedIn posts for lead generation.

Generates professional posts based on business goals and saves them to the vault
for review and scheduling.

Usage:
    python linkedin_poster.py /path/to/vault --draft     # Generate draft post
    python linkededin_poster.py /path/to/vault --list    # List recent posts
    python linkedin_poster.py /path/to/vault --publish   # Publish scheduled posts

Example:
    python linkedin_poster.py ./AI_Employee_Vault --draft
"""

import sys
import json
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

# Post templates for different content types
POST_TEMPLATES = {
    'tip': [
        {
            'hook': '🚀 Quick Tip:',
            'body': 'Did you know the average professional spends 2.5 hours daily on repetitive tasks?',
            'list': [
                '✅ Email responses',
                '✅ Meeting scheduling',
                '✅ Invoice generation',
                '✅ Social media posting'
            ],
            'cta': 'Start small. Pick ONE task. Automate it. Reclaim your time.',
            'question': "What's the first task you'd automate? Drop a comment! 👇"
        },
        {
            'hook': '💡 Productivity Hack:',
            'body': 'Stop manually copying data between apps. Here\'s what smart businesses do:',
            'list': [
                '1. Connect apps with automation tools',
                '2. Set up triggers and actions',
                '3. Let data flow automatically',
                '4. Focus on analysis, not entry'
            ],
            'cta': 'Your brain is for thinking, not copying.',
            'question': 'What repetitive task frustrates you most?'
        },
        {
            'hook': '⚡ Time-Saver Tuesday:',
            'body': 'Here\'s a 5-minute setup that saves hours every week:',
            'list': [
                '→ Create email templates for common responses',
                '→ Use filters to auto-sort incoming mail',
                '→ Set up auto-responders for FAQs',
                '→ Schedule emails to send later'
            ],
            'cta': 'Small changes, big impact.',
            'question': 'What\'s your best email productivity tip?'
        }
    ],
    'question': [
        {
            'hook': '💬 Let\'s Discuss:',
            'body': "What's your biggest challenge with automation?",
            'elaboration': 'I hear from many businesses that they want to automate but don\'t know where to start.',
            'question': 'Share your #1 automation challenge in the comments! Let\'s solve it together. 👇'
        },
        {
            'hook': '🤔 Question for Entrepreneurs:',
            'body': 'How many hours per week do you spend on tasks that could be automated?',
            'elaboration': 'Be honest. I\'m guessing it\'s more than you\'d like to admit.',
            'question': 'Drop a number in the comments. Let\'s see if we can help you cut it in half!'
        },
        {
            'hook': '📊 Poll Time:',
            'body': 'What tool has transformed your productivity the MOST?',
            'options': [
                'A) Email automation',
                'B) Calendar scheduling',
                'C) Project management software',
                'D) AI assistants'
            ],
            'question': 'Vote with your letter in the comments!'
        }
    ],
    'insight': [
        {
            'hook': '💡 Industry Insight:',
            'body': "Here's what I learned after automating 50+ business processes:",
            'insights': [
                'The biggest ROI comes from automating tasks you do daily, not weekly.',
                'Start with customer-facing processes – they compound fastest.',
                'The best automation is invisible – it just works.'
            ],
            'cta': 'What process would you automate first?',
            'question': 'Drop a comment below!'
        },
        {
            'hook': '📈 Trend Alert:',
            'body': 'AI automation isn\'t replacing jobs. It\'s replacing tasks.',
            'elaboration': 'And that\'s a GOOD thing. Humans are meant for strategy, creativity, and relationships – not data entry.',
            'question': 'What task are you glad you don\'t do manually anymore?'
        }
    ],
    'announcement': [
        {
            'hook': '📢 Exciting News!',
            'body': "We're helping more businesses automate their workflows than ever before.",
            'details': 'This month alone, we\'ve saved our clients 500+ hours through smart automation.',
            'cta': 'Ready to join them?',
            'question': 'DM me to get started!'
        }
    ]
}

# Hashtags by category
HASHTAGS = {
    'automation': ['#Automation', '#WorkflowAutomation', '#ProcessImprovement'],
    'productivity': ['#Productivity', '#TimeManagement', '#Efficiency'],
    'business': ['#BusinessTips', '#Entrepreneurship', '#SmallBusiness'],
    'technology': ['#Technology', '#DigitalTransformation', '#Innovation'],
    'ai': ['#AI', '#ArtificialIntelligence', '#MachineLearning']
}


class LinkedInPoster:
    """Generate and manage LinkedIn posts."""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path).resolve()
        self.social_folder = self.vault_path / 'Social'
        self.drafts_folder = self.social_folder / 'drafts'
        self.scheduled_folder = self.social_folder / 'scheduled'
        self.published_folder = self.social_folder / 'published'
        
        # Ensure folders exist
        for folder in [self.social_folder, self.drafts_folder, 
                       self.scheduled_folder, self.published_folder]:
            folder.mkdir(parents=True, exist_ok=True)
        
        # Load config
        self.config = self._load_config()
    
    def _load_config(self) -> dict:
        """Load LinkedIn configuration."""
        config_path = self.vault_path / '.linkedin_config.json'
        if config_path.exists():
            return json.loads(config_path.read_text())
        
        # Default config
        return {
            'post_frequency': 'daily',
            'post_time': '09:00',
            'content_types': ['tip', 'question', 'insight'],
            'hashtags': list(HASHTAGS.values())[0][:3],
            'require_approval': True,
            'auto_approve_themes': ['tips', 'insights']
        }
    
    def generate_post(self, content_type: str = None) -> Path:
        """Generate a new LinkedIn post draft."""
        # Select random content type if not specified
        if content_type is None:
            content_type = random.choice(self.config.get('content_types', ['tip']))
        
        # Get template
        templates = POST_TEMPLATES.get(content_type, POST_TEMPLATES['tip'])
        template = random.choice(templates)
        
        # Build post content
        lines = [template['hook'], '', template['body']]
        
        if 'list' in template:
            lines.append('')
            lines.extend(template['list'])
        
        if 'elaboration' in template:
            lines.append('')
            lines.append(template['elaboration'])
        
        if 'insights' in template:
            lines.append('')
            lines.extend(template['insights'])
        
        if 'options' in template:
            lines.append('')
            lines.extend(template['options'])
        
        if 'details' in template:
            lines.append('')
            lines.append(template['details'])
        
        if 'cta' in template:
            lines.append('')
            lines.append(template['cta'])
        
        if 'question' in template:
            lines.append('')
            lines.append(template['question'])
        
        post_text = '\n'.join(lines)
        
        # Select hashtags
        selected_hashtags = random.sample(
            self.config.get('hashtags', ['#AI', '#Automation', '#Productivity']),
            min(3, len(self.config.get('hashtags', [])))
        )
        hashtag_line = ' '.join(selected_hashtags)
        
        # Create draft file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"LINKEDIN_{content_type}_{timestamp}.md"
        filepath = self.drafts_folder / filename
        
        # Determine if auto-approve eligible
        auto_approve = content_type in self.config.get('auto_approve_themes', [])
        
        draft_content = f'''---
type: social_post
platform: linkedin
created: {datetime.now().isoformat()}
scheduled: {(datetime.now() + timedelta(hours=1)).isoformat()}
status: draft
content_type: {content_type}
auto_approve: {str(auto_approve).lower()}
---

# LinkedIn Post Draft

## Content

{post_text}

## Hashtags
{hashtag_line}

## Engagement Goal
- Target: 100+ impressions, 10+ comments
- CTA: See question above

## Approval Required
{"✅ Auto-approve eligible (matches approved themes)" if auto_approve else "⚠️ Yes - Move to /Approved to publish"}

---

*Generated by AI Employee v0.1 (Silver Tier)*
'''
        filepath.write_text(draft_content, encoding='utf-8')
        
        return filepath
    
    def list_posts(self, limit: int = 5) -> List[Dict]:
        """List recent posts."""
        posts = []
        
        # Check all folders
        for folder in [self.drafts_folder, self.scheduled_folder, self.published_folder]:
            if folder.exists():
                for f in sorted(folder.glob('*.md'), reverse=True)[:limit]:
                    posts.append({
                        'file': f.name,
                        'folder': folder.name,
                        'path': str(f)
                    })
        
        return posts[:limit]
    
    def publish_post(self, post_path: Path) -> bool:
        """Simulate publishing a post (for Silver Tier, just logs the action)."""
        content = post_path.read_text()
        
        # Log publication
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'action': 'linkedin_post_published',
            'file': post_path.name,
            'status': 'success',
            'platform': 'linkedin'
        }
        
        log_file = self.published_folder / f'{datetime.now().strftime("%Y-%m-%d")}.json'
        if log_file.exists():
            logs = json.loads(log_file.read_text())
        else:
            logs = []
        logs.append(log_entry)
        log_file.write_text(json.dumps(logs, indent=2))
        
        return True


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Post Generator')
    parser.add_argument('vault_path', help='Path to Obsidian vault')
    parser.add_argument('--draft', action='store_true', help='Generate draft post')
    parser.add_argument('--type', choices=['tip', 'question', 'insight', 'announcement'],
                       help='Post type (default: random)')
    parser.add_argument('--list', action='store_true', help='List recent posts')
    parser.add_argument('--publish', action='store_true', help='Publish scheduled posts')
    
    args = parser.parse_args()
    
    vault_path = Path(args.vault_path).resolve()
    
    if not vault_path.exists():
        print(f'Error: Vault not found: {vault_path}')
        sys.exit(1)
    
    poster = LinkedInPoster(str(vault_path))
    
    if args.list:
        posts = poster.list_posts()
        print(f"\nRecent LinkedIn Posts ({len(posts)} total):\n")
        print("-" * 60)
        for post in posts:
            print(f"📝 {post['file']}")
            print(f"   Folder: {post['folder']}")
            print()
    
    elif args.draft:
        filepath = poster.generate_post(args.type)
        print(f"\n✅ Draft created: {filepath.name}")
        print(f"   Location: {filepath}")
        print(f"\nNext steps:")
        print(f"1. Review the draft in Obsidian")
        print(f"2. Move to /Social/scheduled/ to publish")
        print(f"3. Or move to /Pending_Approval/ for approval")
    
    elif args.publish:
        # Publish all scheduled posts
        published = 0
        for post_file in poster.scheduled_folder.glob('*.md'):
            if poster.publish_post(post_file):
                print(f"✅ Published: {post_file.name}")
                published += 1
        
        if published == 0:
            print("No scheduled posts to publish.")
        else:
            print(f"\n🎉 Published {published} post(s)")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
