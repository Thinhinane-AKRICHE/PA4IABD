// lib/api.ts
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export const TravelBuddyAPI = {
  async login(email: string, password: string) {
    const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Erreur de connexion');
    }

    const data = await response.json();
    
    // Sauvegarde le token dans un cookie sécurisé
    if (typeof document !== 'undefined') {
      document.cookie = `authToken=${data.token}; path=/; max-age=86400; SameSite=Strict`;
      localStorage.setItem('authToken', data.token);
      if (data.user) {
        localStorage.setItem('user', JSON.stringify(data.user));
      }
    }
    
    return data;
  },

  async logout() {
    if (typeof window !== 'undefined') {
      localStorage.removeItem('authToken');
      localStorage.removeItem('user');
      document.cookie = 'authToken=; path=/; max-age=0';
    }
  },

  getToken() {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('authToken');
    }
    return null;
  },

  isAuthenticated() {
    return !!this.getToken();
  },

  // Ajout de la méthode healthCheck
  async healthCheck() {
    try {
      const response = await fetch(`${API_BASE_URL}/api/health`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        return { status: 'offline' };
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Health check failed:', error);
      return { status: 'offline' };
    }
  },

  // Méthodes supplémentaires utiles
  async sendMessage(message: string, conversationId?: string) {
    const token = this.getToken();
    
    const response = await fetch(`${API_BASE_URL}/api/chat/message`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({ 
        message,
        conversation_id: conversationId 
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Erreur lors de l\'envoi du message');
    }

    return response.json();
  },

  async getConversationHistory(conversationId: string) {
    const token = this.getToken();
    
    const response = await fetch(
      `${API_BASE_URL}/api/chat/history/${conversationId}`,
      {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      }
    );

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Erreur lors de la récupération de l\'historique');
    }

    return response.json();
  },

  async getUserProfile() {
    const token = this.getToken();
    
    const response = await fetch(`${API_BASE_URL}/api/user/profile`, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.message || 'Erreur lors de la récupération du profil');
    }

    return response.json();
  }
};