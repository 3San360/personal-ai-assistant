import { Injectable } from '@angular/core';
import { HttpClient, HttpHeaders, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError, BehaviorSubject } from 'rxjs';
import { catchError, map, retry } from 'rxjs/operators';

import { environment } from '@environments/environment';
import { 
  ChatMessage, 
  ChatResponse, 
  ApiResponse, 
  Conversation, 
  UserPreferences,
  ChatSuggestion 
} from '@app/models';

@Injectable({
  providedIn: 'root'
})
export class ChatService {
  private readonly apiUrl = environment.apiUrl;
  private readonly httpOptions = {
    headers: new HttpHeaders({
      'Content-Type': 'application/json'
    })
  };

  // Current conversation state
  private currentConversationSubject = new BehaviorSubject<Conversation | null>(null);
  public currentConversation$ = this.currentConversationSubject.asObservable();

  // Chat messages state
  private messagesSubject = new BehaviorSubject<ChatMessage[]>([]);
  public messages$ = this.messagesSubject.asObservable();

  // Typing indicator state
  private isTypingSubject = new BehaviorSubject<boolean>(false);
  public isTyping$ = this.isTypingSubject.asObservable();

  constructor(private http: HttpClient) {}

  /**
   * Send a message to the AI assistant
   */
  sendMessage(
    message: string, 
    conversationId?: string, 
    userPreferences?: UserPreferences
  ): Observable<ApiResponse<ChatResponse>> {
    const payload = {
      message: message.trim(),
      conversation_id: conversationId,
      user_preferences: userPreferences || {}
    };

    // Add user message to local state immediately
    this.addMessage({
      id: this.generateMessageId(),
      content: message,
      timestamp: new Date(),
      isUser: true,
      messageType: 'text'
    });

    // Show typing indicator
    this.setTyping(true);

    return this.http.post<ApiResponse<ChatResponse>>(
      `${this.apiUrl}/chat/message`,
      payload,
      this.httpOptions
    ).pipe(
      map(response => {
        if (response.success && response.data) {
          // Add assistant response to local state
          this.addMessage({
            id: this.generateMessageId(),
            content: response.data.message,
            timestamp: response.data.timestamp,
            isUser: false,
            messageType: 'text',
            metadata: {
              responseType: response.data.responseType,
              confidence: response.data.confidence,
              actionsTaken: response.data.actionsTaken,
              suggestions: response.data.suggestions
            }
          });

          // Update conversation ID if provided
          if (response.metadata?.conversation_id) {
            this.updateConversationId(response.metadata.conversation_id);
          }
        }
        
        this.setTyping(false);
        return response;
      }),
      retry(1),
      catchError(error => {
        this.setTyping(false);
        return this.handleError(error);
      })
    );
  }

  /**
   * Get conversation history
   */
  getConversationHistory(conversationId: string, limit: number = 20): Observable<ChatMessage[]> {
    return this.http.get<ApiResponse<{messages: any[]}>>(
      `${this.apiUrl}/chat/conversation/${conversationId}/history?limit=${limit}`
    ).pipe(
      map(response => {
        if (response.success && response.data) {
          return response.data.messages.map(msg => ({
            id: msg.id,
            content: msg.content,
            timestamp: new Date(msg.timestamp),
            isUser: msg.is_user,
            messageType: msg.message_type,
            metadata: msg.metadata
          }));
        }
        return [];
      }),
      catchError(this.handleError)
    );
  }

  /**
   * Create a new conversation
   */
  createConversation(userPreferences?: UserPreferences): Observable<ApiResponse<{conversation_id: string}>> {
    const payload = {
      user_preferences: userPreferences || {}
    };

    return this.http.post<ApiResponse<{conversation_id: string}>>(
      `${this.apiUrl}/chat/conversation/new`,
      payload,
      this.httpOptions
    ).pipe(
      map(response => {
        if (response.success && response.data?.conversation_id) {
          this.updateConversationId(response.data.conversation_id);
        }
        return response;
      }),
      catchError(this.handleError)
    );
  }

  /**
   * Get conversation information
   */
  getConversationInfo(conversationId: string): Observable<ApiResponse<{conversation: Conversation}>> {
    return this.http.get<ApiResponse<{conversation: Conversation}>>(
      `${this.apiUrl}/chat/conversation/${conversationId}`
    ).pipe(
      map(response => {
        if (response.success && response.data?.conversation) {
          const conv = response.data.conversation;
          this.currentConversationSubject.next({
            id: conv.id,
            createdAt: new Date(conv.createdAt),
            updatedAt: new Date(conv.updatedAt),
            messageCount: conv.messageCount,
            context: conv.context,
            userPreferences: conv.userPreferences
          });
        }
        return response;
      }),
      catchError(this.handleError)
    );
  }

  /**
   * Get chat suggestions
   */
  getSuggestions(): Observable<ChatSuggestion[]> {
    return this.http.get<ApiResponse<{suggestions: ChatSuggestion[]}>>(
      `${this.apiUrl}/chat/suggestions`
    ).pipe(
      map(response => {
        if (response.success && response.data?.suggestions) {
          return response.data.suggestions;
        }
        return this.getDefaultSuggestions();
      }),
      catchError(() => {
        // Return default suggestions on error
        return [this.getDefaultSuggestions()];
      })
    );
  }

  /**
   * Clear current conversation
   */
  clearConversation(): void {
    this.messagesSubject.next([]);
    this.currentConversationSubject.next(null);
    this.setTyping(false);
  }

  /**
   * Add a message to the current conversation
   */
  private addMessage(message: ChatMessage): void {
    const currentMessages = this.messagesSubject.value;
    this.messagesSubject.next([...currentMessages, message]);
  }

  /**
   * Update conversation ID
   */
  private updateConversationId(conversationId: string): void {
    const currentConv = this.currentConversationSubject.value;
    if (currentConv) {
      this.currentConversationSubject.next({
        ...currentConv,
        id: conversationId
      });
    } else {
      this.currentConversationSubject.next({
        id: conversationId,
        createdAt: new Date(),
        updatedAt: new Date(),
        messageCount: 0,
        context: {},
        userPreferences: {}
      });
    }
  }

  /**
   * Set typing indicator state
   */
  private setTyping(isTyping: boolean): void {
    if (isTyping) {
      setTimeout(() => {
        this.isTypingSubject.next(true);
      }, environment.chat.typingIndicatorDelay);
    } else {
      this.isTypingSubject.next(false);
    }
  }

  /**
   * Generate unique message ID
   */
  private generateMessageId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }

  /**
   * Get default suggestions when API is unavailable
   */
  private getDefaultSuggestions(): ChatSuggestion[] {
    return [
      {
        text: "What's the weather like today?",
        category: 'weather',
        description: 'Get current weather information'
      },
      {
        text: "Show me the latest news",
        category: 'news',
        description: 'Get current news headlines'
      },
      {
        text: "What's on my calendar today?",
        category: 'calendar',
        description: 'View today\'s calendar events'
      },
      {
        text: "Help - what can you do?",
        category: 'help',
        description: 'Learn about available features'
      }
    ];
  }

  /**
   * Handle HTTP errors
   */
  private handleError(error: HttpErrorResponse): Observable<never> {
    let errorMessage = 'An error occurred';
    
    if (error.error instanceof ErrorEvent) {
      // Client-side error
      errorMessage = `Error: ${error.error.message}`;
    } else {
      // Server-side error
      errorMessage = error.error?.error || `Error ${error.status}: ${error.message}`;
    }

    console.error('ChatService error:', errorMessage);
    return throwError(() => new Error(errorMessage));
  }

  /**
   * Get current conversation ID
   */
  get currentConversationId(): string | null {
    return this.currentConversationSubject.value?.id || null;
  }

  /**
   * Get current messages
   */
  get currentMessages(): ChatMessage[] {
    return this.messagesSubject.value;
  }
}
