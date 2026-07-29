import {useState, useEffect} from 'react';
import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
import Heading from '@theme/Heading';
import styles from './index.module.css';

/* --------------------------------------------------------------------------
   Particle background component
   -------------------------------------------------------------------------- */
function Particles() {
  const [particles] = useState(() =>
    Array.from({length: 25}, (_, i) => ({
      id: i,
      left: `${Math.random() * 100}%`,
      top: `${Math.random() * 100}%`,
      size: Math.random() * 3 + 1.5,
      duration: `${Math.random() * 4 + 3}s`,
      delay: `${Math.random() * 3}s`,
      color: ['#A78BFA', '#22D3EE', '#EC4899', '#34D399'][Math.floor(Math.random() * 4)],
    }))
  );

  return (
    <div className={styles.particleContainer}>
      {particles.map((p) => (
        <span
          key={p.id}
          className={styles.particle}
          style={{
            left: p.left,
            top: p.top,
            width: p.size,
            height: p.size,
            background: p.color,
            opacity: 0,
            animation: `float ${p.duration} ${p.delay} ease-in-out infinite`,
            boxShadow: `0 0 6px ${p.color}`,
          }}
        />
      ))}
    </div>
  );
}

/* --------------------------------------------------------------------------
   Homepage header — the Hero
   -------------------------------------------------------------------------- */
function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();

  return (
    <header className={clsx('hero', styles.heroBanner)}>
      <Particles />

      <div className="container">
        <div className={styles.heroContent}>
          {/* --- Left: text --- */}
          <div className={styles.heroText}>
            <Heading as="h1" className={styles.heroTitle}>
              {siteConfig.title}
            </Heading>
            <p className={styles.heroSubtitle}>
              {siteConfig.tagline}
              <span className={styles.typingCursor} />
            </p>

            {/* Buttons */}
            <div className={styles.buttons}>
              <Link
                className={`button button--lg ${styles.primaryButton}`}
                to="/docs/intro"
              >
                Get Started → 5 min
              </Link>
              <Link
                className={`button button--lg ${styles.secondaryButton}`}
                to="https://github.com/MahaMeher/Hackathon-1-Book"
              >
                View on GitHub
              </Link>
            </div>

            {/* Stats bar */}
            <div className={styles.statsBar}>
              <div className={styles.statItem}>
                <span className={styles.statValue}>04</span>
                <span className={styles.statLabel}>Modules</span>
              </div>
              <div className={styles.statDivider} />
              <div className={styles.statItem}>
                <span className={styles.statValue}>ROS 2</span>
                <span className={styles.statLabel}>Framework</span>
              </div>
              <div className={styles.statDivider} />
              <div className={styles.statItem}>
                <span className={styles.statValue}>AI</span>
                <span className={styles.statLabel}>Powered</span>
              </div>
              <div className={styles.statDivider} />
              <div className={styles.statItem}>
                <span className={styles.statValue}>VLA</span>
                <span className={styles.statLabel}>Vision-Language-Action</span>
              </div>
            </div>
          </div>

          {/* --- Right: robot + tech badges --- */}
          <div className={styles.heroImageSection}>
            <div className={styles.orbitalRing} />
            <div className={styles.orbitalRing2} />

            {/* Orbital dots */}
            <span className={styles.orbitDot} style={{top: '15%', left: '50%'}} />
            <span className={styles.orbitDot2} style={{bottom: '20%', right: '10%'}} />

            {/* Floating tech badges */}
            <span className={`${styles.floatingBadge} ${styles.badgeRos}`}>
              <span className={styles.badgeDot} style={{background: '#EF4444'}} />
              ROS 2
            </span>
            <span className={`${styles.floatingBadge} ${styles.badgeAi}`}>
              <span className={styles.badgeDot} style={{background: '#6366F1'}} />
              Neural AI
            </span>
            <span className={`${styles.floatingBadge} ${styles.badgePython}`}>
              <span className={styles.badgeDot} style={{background: '#34D399'}} />
              Python
            </span>
            <span className={`${styles.floatingBadge} ${styles.badgeIsaac}`}>
              <span className={styles.badgeDot} style={{background: '#EC4899'}} />
              NVIDIA Isaac
            </span>

            {/* Robot image */}
            <div className={styles.heroImageWrapper}>
              <img
                src="/img/robot-ai-icon.svg"
                alt="Robot AI Integration"
                className={styles.featureImage}
              />
            </div>
          </div>
        </div>
      </div>
    </header>
  );
}

/* --------------------------------------------------------------------------
   Features section
   -------------------------------------------------------------------------- */
const features = [
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
        <circle cx="9" cy="7" r="4" />
        <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
        <path d="M16 3.13a4 4 0 0 1 0 7.75" />
      </svg>
    ),
    title: 'For AI Students',
    desc: 'Designed specifically for students with Python knowledge but beginner robotics experience.',
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16z" />
        <path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z" />
        <path d="M12 2v2" />
        <path d="M12 22v-2" />
        <path d="m17 20.66-1-1.73" />
        <path d="M11 10.27 7 3.34" />
        <path d="m20.66 17-1.73-1" />
        <path d="m3.34 7 1.73 1" />
        <path d="M14 12h8" />
        <path d="m2 12 3 3" />
        <path d="m2 12 3-3" />
      </svg>
    ),
    title: 'Practical Focus',
    desc: 'Learn through hands-on examples connecting AI agents to ROS controllers.',
  },
  {
    icon: (
      <svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 8V4H8" />
        <rect width="16" height="12" x="4" y="8" rx="2" />
        <path d="M2 14h2" />
        <path d="M20 14h2" />
        <path d="M15 13v2" />
        <path d="M9 13v2" />
      </svg>
    ),
    title: 'Humanoid Robotics',
    desc: 'Specialized content for understanding the middleware that enables humanoid robot control.',
  },
];

function FeaturesSection() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="text--center padding-horiz--md" style={{marginBottom: '3rem'}}>
          <h2>Master the Future of Robotics</h2>
          <p style={{fontSize: '1.15rem', maxWidth: '700px', margin: '0 auto', color: '#475569'}}>
            Learn how to build intelligent humanoid robots that understand natural language,
            perceive their environment, and execute complex tasks autonomously.
          </p>
        </div>
        <div className="row">
          {features.map((f, i) => (
            <div className="col col--4" key={i}>
              <div className={styles.featureCard}>
                <div className={styles.featureIcon}>{f.icon}</div>
                <h3>{f.title}</h3>
                <p>{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

/* --------------------------------------------------------------------------
   Modules section
   -------------------------------------------------------------------------- */
const modules = [
  {num: 'Module 1', title: 'The Robotic Nervous System', desc: 'ROS 2 — the middleware that connects sensors, actuators, and AI in modern robots.', to: '/docs/module1'},
  {num: 'Module 2', title: 'The Digital Twin', desc: 'Gazebo & Unity — simulate, test, and validate robotic behaviors before real-world deployment.', to: '/docs/module2'},
  {num: 'Module 3', title: 'The AI-Robot Brain', desc: 'NVIDIA Isaac — GPU-accelerated perception, manipulation, and control for humanoid robots.', to: '/docs/module3'},
  {num: 'Module 4', title: 'Vision-Language-Action', desc: 'VLA models — bridge LLMs and robot control so robots understand and act on natural language.', to: '/docs/module4'},
];

function ModulesSection() {
  return (
    <section className={styles.modulesSection}>
      <div className="container">
        <div className="text--center padding-horiz--md">
          <h2>Learning Modules</h2>
          <p className={styles.modulesSubtitle}>A step-by-step journey from ROS basics to advanced VLA systems</p>
          <div className="row">
            {modules.map((m, i) => (
              <div className="col col--3" key={i}>
                <Link to={m.to} className={styles.moduleCard}>
                  <span className={styles.moduleNumber}>{m.num}</span>
                  <h3>{m.title}</h3>
                  <p>{m.desc}</p>
                  <span className={styles.moduleArrow}>→</span>
                </Link>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

/* --------------------------------------------------------------------------
   Page
   -------------------------------------------------------------------------- */
export default function Home() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`Welcome to ${siteConfig.title}`}
      description="A comprehensive guide to ROS 2 for AI students"
    >
      <HomepageHeader />
      <main>
        <FeaturesSection />
        <ModulesSection />
      </main>
    </Layout>
  );
}
