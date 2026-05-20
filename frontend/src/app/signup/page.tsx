'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function SignupPage() {
  const router = useRouter();
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    if (formData.password !== formData.confirmPassword) {
      setError('Les mots de passe ne correspondent pas');
      setIsLoading(false);
      return;
    }

    try {
      // Simulation inscription
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      localStorage.setItem('user', JSON.stringify({ 
        name: formData.name,
        email: formData.email 
      }));
      router.push('/');
    } catch (err) {
      setError('Erreur lors de l\'inscription');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F5F5F0] flex items-center justify-center p-4">
      <div className="absolute inset-0 overflow-hidden">
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-[#D4C5B0] rounded-full opacity-10 blur-3xl"></div>
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-[#C4B5A0] rounded-full opacity-10 blur-3xl"></div>
      </div>

      <div className="relative w-full max-w-md">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-gradient-to-br from-[#D4C5B0] to-[#C4B5A0] rounded-2xl mb-4 shadow-lg">
            <span className="text-3xl">✈️</span>
          </div>
          <h1 className="text-3xl font-semibold text-[#2D2D2D] mb-2">Créer un compte</h1>
          <p className="text-[#666]">Commencez votre aventure avec TravelBuddy</p>
        </div>

        <div className="bg-white rounded-2xl shadow-lg border border-[#E5E5DC] p-8">
          <form onSubmit={handleSignup} className="space-y-5">
            <div>
              <label className="block text-sm font-medium text-[#2D2D2D] mb-2">
                Nom complet
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({...formData, name: e.target.value})}
                placeholder="Jean Dupont"
                required
                className="w-full px-4 py-3 bg-[#F5F5F0] border border-[#E5E5DC] rounded-xl focus:outline-none focus:border-[#C4B5A0] focus:bg-white transition-all text-[#2D2D2D]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[#2D2D2D] mb-2">
                Adresse email
              </label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({...formData, email: e.target.value})}
                placeholder="vous@exemple.com"
                required
                className="w-full px-4 py-3 bg-[#F5F5F0] border border-[#E5E5DC] rounded-xl focus:outline-none focus:border-[#C4B5A0] focus:bg-white transition-all text-[#2D2D2D]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[#2D2D2D] mb-2">
                Mot de passe
              </label>
              <input
                type="password"
                value={formData.password}
                onChange={(e) => setFormData({...formData, password: e.target.value})}
                placeholder="••••••••"
                required
                className="w-full px-4 py-3 bg-[#F5F5F0] border border-[#E5E5DC] rounded-xl focus:outline-none focus:border-[#C4B5A0] focus:bg-white transition-all text-[#2D2D2D]"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-[#2D2D2D] mb-2">
                Confirmer le mot de passe
              </label>
              <input
                type="password"
                value={formData.confirmPassword}
                onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
                placeholder="••••••••"
                required
                className="w-full px-4 py-3 bg-[#F5F5F0] border border-[#E5E5DC] rounded-xl focus:outline-none focus:border-[#C4B5A0] focus:bg-white transition-all text-[#2D2D2D]"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-xl text-sm">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={isLoading}
              className="w-full bg-[#2D2D2D] text-white py-3 rounded-xl font-medium hover:bg-[#1a1a1a] disabled:opacity-50 transition-all shadow-lg"
            >
              {isLoading ? 'Création...' : 'Créer mon compte'}
            </button>
          </form>

          <p className="mt-6 text-center text-sm text-[#666]">
            Déjà un compte ?{' '}
            <a href="/login" className="text-[#2D2D2D] font-medium hover:underline">
              Se connecter
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}