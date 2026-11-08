import React from "react";

export const metadata = {
  title: "دستیار هوشمند زیرساخت و مهندسی قابلیت اطمینان (SRE) لیارا",
  description:
    "تجربه تک‌کلیکی دیپلوی (Zero-Friction)، حلقه خودترمیم‌گر خطای بیلد (Auto-Build-Fix) و عیب‌یابی موازی خطای HTTP 500 با deepseek-v4.1-flash و Mizan-4B/Jev",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fa" dir="rtl" className="dark">
      <head>
        <link
          rel="stylesheet"
          href="https://cdn.jsdelivr.net/gh/rastikerdar/vazirmatn@v33.003/Vazirmatn-font-face.css"
        />
      </head>
      <body
        style={{ fontFamily: "'Vazirmatn', sans-serif" }}
        className="bg-slate-950 text-slate-100 min-h-screen antialiased selection:bg-sky-500 selection:text-white"
      >
        {children}
      </body>
    </html>
  );
}
