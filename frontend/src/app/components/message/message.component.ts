import { Component, Input, OnInit } from '@angular/core';
import { Message } from '../models/message.model';

@Component({
  selector: 'app-message',
  templateUrl: './message.component.html',
  styleUrls: ['./message.component.scss']
})
export class MessageComponent implements OnInit {
  @Input() message!: Message;
  @Input() isLatest: boolean = false;

  ngOnInit(): void {
    // Component initialization logic if needed
  }

  /**
   * Format timestamp for display
   */
  formatTimestamp(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMinutes / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMinutes < 1) {
      return 'Just now';
    } else if (diffMinutes < 60) {
      return `${diffMinutes}m ago`;
    } else if (diffHours < 24) {
      return `${diffHours}h ago`;
    } else if (diffDays < 7) {
      return `${diffDays}d ago`;
    } else {
      return date.toLocaleDateString();
    }
  }

  /**
   * Check if message contains code blocks
   */
  hasCodeBlocks(): boolean {
    return this.message.content.includes('```');
  }

  /**
   * Parse message content with code blocks
   */
  parseMessageContent(): Array<{type: 'text' | 'code', content: string, language?: string}> {
    const parts: Array<{type: 'text' | 'code', content: string, language?: string}> = [];
    const codeBlockRegex = /```(\w+)?\n([\s\S]*?)```/g;
    let lastIndex = 0;
    let match;

    while ((match = codeBlockRegex.exec(this.message.content)) !== null) {
      // Add text before code block
      if (match.index > lastIndex) {
        const textContent = this.message.content.substring(lastIndex, match.index);
        if (textContent.trim()) {
          parts.push({ type: 'text', content: textContent });
        }
      }

      // Add code block
      parts.push({
        type: 'code',
        content: match[2],
        language: match[1] || 'text'
      });

      lastIndex = match.index + match[0].length;
    }

    // Add remaining text
    if (lastIndex < this.message.content.length) {
      const textContent = this.message.content.substring(lastIndex);
      if (textContent.trim()) {
        parts.push({ type: 'text', content: textContent });
      }
    }

    // If no code blocks found, return the entire content as text
    if (parts.length === 0) {
      parts.push({ type: 'text', content: this.message.content });
    }

    return parts;
  }

  /**
   * Copy code to clipboard
   */
  copyCode(code: string): void {
    navigator.clipboard.writeText(code).then(() => {
      // Could add a toast notification here
      console.log('Code copied to clipboard');
    }).catch(err => {
      console.error('Failed to copy code:', err);
    });
  }

  /**
   * Handle link clicks in message content
   */
  onLinkClick(event: Event, url: string): void {
    event.preventDefault();
    // Open external links in new tab
    if (url.startsWith('http')) {
      window.open(url, '_blank', 'noopener,noreferrer');
    }
  }

  /**
   * Get message status icon
   */
  getStatusIcon(): string {
    if (this.message.sender === 'user') {
      return this.message.status === 'sent' ? 'check' : 'schedule';
    }
    return '';
  }

  /**
   * Get avatar initials
   */
  getAvatarInitials(): string {
    if (this.message.sender === 'user') {
      return 'U';
    } else {
      return 'AI';
    }
  }

  /**
   * Get message bubble class
   */
  getMessageClass(): string {
    const baseClass = 'message-bubble';
    const senderClass = this.message.sender === 'user' ? 'user-message' : 'assistant-message';
    const latestClass = this.isLatest ? 'latest-message' : '';
    
    return `${baseClass} ${senderClass} ${latestClass}`.trim();
  }
}
