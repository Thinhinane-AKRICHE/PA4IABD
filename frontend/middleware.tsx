// middleware.ts - VERSION DÉSACTIVÉE
// 
// ⚠️ Ce middleware est désactivé car il crée une boucle de redirection
// Le token est stocké dans localStorage (côté client), pas dans les cookies
// Le middleware tourne côté serveur et ne peut pas accéder à localStorage
//
// SOLUTION: Gérer l'auth côté client uniquement dans les pages

import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  // ✅ Laisser passer toutes les requêtes
  // L'authentification est gérée côté client dans les pages
  return NextResponse.next();
}

// Désactiver le matcher pour qu'il ne s'applique à aucune route
export const config = {
  matcher: [],
};

/* 
  ANCIENNE VERSION (NE PAS UTILISER) :

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (pathname.startsWith('/chat')) {
    const token = request.cookies.get('authToken')?.value;
    if (!token) {
      const loginUrl = new URL('/login', request.url);
      return NextResponse.redirect(loginUrl);
    }
  }

  if (pathname === '/login') {
    const token = request.cookies.get('authToken')?.value;
    if (token) {
      const chatUrl = new URL('/chat', request.url);
      return NextResponse.redirect(chatUrl);
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/chat/:path*', '/login'],
};
*/