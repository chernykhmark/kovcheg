import React, { useEffect, useMemo, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { motion, useReducedMotion } from 'framer-motion'
import { ChevronDown, Clock3, Disc3, MessageCircle, Send, Sparkles, Volume2 } from 'lucide-react'
import { eventConfig } from './config'
import { artists, program } from './data'
import { translations } from './i18n'
import './styles.css'

const reveal = { hidden: { opacity: 0, y: 22 }, show: { opacity: 1, y: 0 } }

function CanvasBackground() {
  const canvasRef = useRef(null)
  useEffect(() => {
    const canvas = canvasRef.current
    const context = canvas.getContext('2d', { alpha: false })
    const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let frame; let visible = !document.hidden; let width; let height
    const amount = window.innerWidth < 640 ? 28 : 64
    const dots = Array.from({ length: amount }, () => ({ x: Math.random(), y: Math.random(), size: Math.random() * 2 + .5, speed: Math.random() * .28 + .08, hue: [190, 278, 326][Math.floor(Math.random() * 3)] }))
    const snow = Array.from({ length: amount }, () => ({ x: Math.random(), y: Math.random(), size: Math.random() * 2.3 + .7, speed: Math.random() * .38 + .16, sway: Math.random() * 2 }))
    const resize = () => { const ratio = Math.min(devicePixelRatio || 1, 2); width = innerWidth; height = innerHeight; canvas.width = width * ratio; canvas.height = height * ratio; canvas.style.width = `${width}px`; canvas.style.height = `${height}px`; context.setTransform(ratio, 0, 0, ratio, 0, 0) }
    const draw = (time = 0) => {
      const gradient = context.createLinearGradient(0, 0, width, height)
      gradient.addColorStop(0, '#0a0a0f'); gradient.addColorStop(.48, '#160e2a'); gradient.addColorStop(1, '#071d2a')
      context.fillStyle = gradient; context.fillRect(0, 0, width, height)
      dots.forEach((p) => { p.y -= p.speed / height; if (p.y < -.1) { p.y = 1.1; p.x = Math.random() }; const x = p.x * width; const y = p.y * height; const glow = context.createRadialGradient(x, y, 0, x, y, p.size * 16); glow.addColorStop(0, `hsla(${p.hue}, 100%, 65%, .35)`); glow.addColorStop(1, `hsla(${p.hue}, 100%, 55%, 0)`); context.fillStyle = glow; context.beginPath(); context.arc(x, y, p.size * 16, 0, Math.PI * 2); context.fill() })
      snow.forEach((p) => { p.y += p.speed / height; if (p.y > 1.05) { p.y = -.05; p.x = Math.random() }; const x = p.x * width + Math.sin(time / 1000 + p.sway) * 12; context.fillStyle = `rgba(232, 251, 255, ${.35 + p.size / 7})`; context.beginPath(); context.arc(x, p.y * height, p.size, 0, Math.PI * 2); context.fill() })
      if (!reduced && visible) frame = requestAnimationFrame(draw)
    }
    const visibility = () => { visible = !document.hidden; if (visible && !reduced) frame = requestAnimationFrame(draw) }
    resize(); draw(); addEventListener('resize', resize); document.addEventListener('visibilitychange', visibility)
    return () => { cancelAnimationFrame(frame); removeEventListener('resize', resize); document.removeEventListener('visibilitychange', visibility) }
  }, [])
  return <canvas ref={canvasRef} className="site-canvas" aria-hidden="true" />
}

function Countdown({ labels }) {
  const [left, setLeft] = useState(() => Math.max(0, new Date(eventConfig.date) - Date.now()))
  useEffect(() => { const timer = setInterval(() => setLeft(Math.max(0, new Date(eventConfig.date) - Date.now())), 1000); return () => clearInterval(timer) }, [])
  const values = useMemo(() => { let s = Math.floor(left / 1000); const days = Math.floor(s / 86400); s %= 86400; const hours = Math.floor(s / 3600); s %= 3600; return [days, hours, Math.floor((s % 3600) / 60), s % 60].map((v) => String(v).padStart(2, '0')) }, [left])
  return <div className="countdown" aria-label="Countdown to event">{values.map((value, index) => <div className="countdown-unit" key={labels[index]}><b>{value}</b><span>{labels[index]}</span></div>)}</div>
}

function BuyButton({ label, className = '' }) { return <a className={`buy-button ${className}`} href={eventConfig.telegramBotUrl} target="_blank" rel="noreferrer"><Send size={18} />{label}</a> }

function Header({ lang, setLang, t }) { return <header className="header"><a href="#top" className="brand" aria-label="To top">NYR<span>27</span></a><nav>{Object.entries(t.nav).map(([id, name]) => <a href={`#${id}`} key={id}>{name}</a>)}</nav><div className="language" aria-label="Language">{['ru', 'en'].map((value) => <button key={value} onClick={() => setLang(value)} className={lang === value ? 'active' : ''}>{value}</button>)}</div></header> }

function App() {
  const [lang, setLang] = useState('ru'); const t = translations[lang]; const reduced = useReducedMotion()
  const icons = [Disc3, Volume2, Clock3]
  useEffect(() => {
    const webApp = window.Telegram?.WebApp
    if (!webApp) return

    webApp.ready()
    webApp.expand()

    // В новых клиентах Telegram разворачиваем Mini App на весь экран.
    // В старых остаётся безопасный вариант — максимальная высота WebView.
    if (webApp.isVersionAtLeast?.('8.0') && !webApp.isFullscreen) {
      webApp.requestFullscreen()
    }
  }, [])
  return <><CanvasBackground /><div className="page" id="top"><Header {...{ lang, setLang, t }} />
    <main>
      <section className="hero section-shell"><motion.div initial="hidden" animate="show" transition={{ staggerChildren: .11 }} className="hero-content"><motion.p variants={reveal} className="eyebrow">{t.heroKicker}</motion.p><motion.h1 variants={reveal}>{eventConfig.name}</motion.h1><motion.p variants={reveal} className="event-meta">{eventConfig.displayDate} <i /> {eventConfig.venue}</motion.p><motion.p variants={reveal} className="hero-sub">{t.heroSub}</motion.p><motion.div variants={reveal}><Countdown labels={t.timerLabels} /></motion.div><motion.div variants={reveal}><BuyButton label={t.buy} /></motion.div></motion.div><a href="#vibe" className="scroll-cue"><span>{t.scroll}</span><ChevronDown size={20} /></a></section>
      <section id="vibe" className="section-shell section"><motion.div initial="hidden" whileInView="show" viewport={{ once: true, amount: .2 }} transition={{ duration: .45 }}><p className="eyebrow">{t.vibeEyebrow}</p><h2>{t.vibeTitle}</h2><div className="vibe-lines">{t.vibeLines.map((line, i) => <p key={line}><span>0{i + 1}</span>{line}</p>)}</div><div className="feature-grid">{t.features.map(([title, description], i) => { const Icon = icons[i]; return <motion.article variants={reveal} key={title} className="glass-card feature"><Icon /><h3>{title}</h3><p>{description}</p></motion.article> })}</div></motion.div></section>
      <section id="lineup" className="section-shell section"><motion.div initial="hidden" whileInView="show" viewport={{ once: true, amount: .12 }} transition={{ duration: .45 }}><motion.p variants={reveal} className="notice-card">{t.newcomerNotice}</motion.p><p className="eyebrow">{t.lineupEyebrow}</p><h2>{t.lineupTitle}</h2><div className="artist-grid">{artists.map((artist) => <motion.article variants={reveal} key={artist.alias} className={`artist-card ${artist.accent}`} whileHover={reduced ? {} : { y: -6 }}><div className="art"><div className="orb" /> <div className="equalizer">{Array.from({ length: 9 }, (_, i) => <i key={i} style={{ '--delay': `${i * .1}s`, '--height': `${28 + ((i * 13) % 55)}%` }} />)}</div></div><div className="artist-info"><span>{artist.time}</span><h3>{artist.alias}</h3><p>{artist.genre}</p></div></motion.article>)}</div></motion.div></section>
      <section id="program" className="section-shell section"><motion.div initial="hidden" whileInView="show" viewport={{ once: true, amount: .2 }} transition={{ duration: .45 }}><p className="eyebrow">{t.programEyebrow}</p><h2>{t.programTitle}</h2><div className="timeline">{program.map((item) => <motion.div variants={reveal} className="timeline-item" key={item.time}><time>{item.time}</time><span className="timeline-dot" /><p>{item.event[lang]}</p></motion.div>)}</div><motion.p variants={reveal} className="notice-card kids-room">{t.kidsRoomNotice}</motion.p><BuyButton label={t.buy} className="program-button" /></motion.div></section>
      <section className="section-shell finale"><motion.div initial="hidden" whileInView="show" viewport={{ once: true, amount: .3 }} transition={{ duration: .45 }} className="finale-box"><Sparkles /><p className="eyebrow">{t.finalEyebrow}</p><h2>{t.finalTitle}</h2><p className="final-meta">{t.finalText}<br />{eventConfig.venue}</p><BuyButton label={t.buy} /></motion.div></section>
    </main><footer><p>© 2026 {eventConfig.name}. {t.copyright}</p><div>{eventConfig.socials.map((social) => <a key={social.label} href={social.url} target="_blank" rel="noreferrer">{social.icon === 'telegram' ? <Send size={15} /> : <MessageCircle size={15} />}{social.label}</a>)}</div></footer><div className="mobile-buy"><BuyButton label={t.buyShort} /></div></div></>
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App /></React.StrictMode>)
