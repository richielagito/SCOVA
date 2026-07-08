/** @type {import('next').NextConfig} */
const backendUrl = process.env.BACKEND_URL || "http://127.0.0.1:5000";

const nextConfig = {
    async rewrites() {
        return [
            {
                source: "/api/:path*",
                destination: `${backendUrl}/api/:path*`,
            },
            {
                source: "/logout",
                destination: `${backendUrl}/logout`,
            },
            {
                source: "/set_session",
                destination: `${backendUrl}/set_session`,
            },
            {
                source: "/create-class",
                destination: `${backendUrl}/create-class`,
            },
            // Backend Pages Proxies
            // Dashboard handled by Next.js
            /*
      {
        source: '/dashboard',
        destination: 'http://127.0.0.1:5000/dashboard',
      },
      */
            {
                source: "/admin",
                destination: `${backendUrl}/admin`,
            },
            {
                source: "/admin/:path*",
                destination: `${backendUrl}/admin/:path*`,
            },
            // Kelas paths handled by Next.js
            /*
      {
        source: '/kelas/:path*',
        destination: 'http://127.0.0.1:5000/kelas/:path*',
      },
      {
        source: '/kelas-murid/:path*',
        destination: 'http://127.0.0.1:5000/kelas-murid/:path*',
      },
      */
            // Static files from Flask (if any specific ones needed, usually /static/...)
            {
                source: "/static/:path*",
                destination: `${backendUrl}/static/:path*`,
            },
        ];
    },
};

export default nextConfig;
