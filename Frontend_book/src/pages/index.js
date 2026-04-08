import clsx from 'clsx';
import Link from '@docusaurus/Link';
import useDocusaurusContext from '@docusaurus/useDocusaurusContext';
import Layout from '@theme/Layout';
// Commenting out HomepageFeatures since we're not using it in this implementation
// import HomepageFeatures from '@site/src/components/HomepageFeatures';

import Heading from '@theme/Heading';
import styles from './index.module.css';

function HomepageHeader() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <header className={clsx('hero hero--primary', styles.heroBanner)}>
      <div className="container">
        <div className={styles.heroContent}>
          <div className={styles.heroText}>
            <Heading as="h1" className="hero__title">
              {siteConfig.title}
            </Heading>
            <p className="hero__subtitle">{siteConfig.tagline}</p>
            <div className={styles.buttons}>
              <Link
                className="button button--secondary button--lg"
                to="/docs/intro">
                Get Started - 5min ⏱️
              </Link>
            </div>
          </div>
          <div className={styles.heroImage}>
            <img
              src="/img/robot-ai-icon.svg"
              alt="Robot AI Integration"
              className={styles.featureImage}
            />
          </div>
        </div>
      </div>
    </header>
  );
}

export default function Home() {
  const {siteConfig} = useDocusaurusContext();
  return (
    <Layout
      title={`Welcome to ${siteConfig.title}`}
      description="A comprehensive guide to ROS 2 for AI students">
      <HomepageHeader />
      <main>
        <section className={styles.features}>
          <div className="container">
            <div className="text--center padding-horiz--md" style={{marginBottom: '3rem'}}>
              <h2>Master the Future of Robotics</h2>
              <p style={{fontSize: '1.2rem', maxWidth: '800px', margin: '0 auto', color: '#475569'}}>
                Learn how to build intelligent humanoid robots that understand natural language,
                perceive their environment, and execute complex tasks autonomously.
              </p>
            </div>
            <div className="row">
              <div className="col col--4">
                <div className="text--center padding-horiz--md">
                  <div className={styles.featureIcon}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"></path>
                      <circle cx="9" cy="7" r="4"></circle>
                      <path d="M23 21v-2a4 4 0 0 0-3-3.87"></path>
                      <path d="M16 3.13a4 4 0 0 1 0 7.75"></path>
                    </svg>
                  </div>
                  <h3>For AI Students</h3>
                  <p>Designed specifically for students with Python knowledge but beginner robotics experience.</p>
                </div>
              </div>
              <div className="col col--4">
                <div className="text--center padding-horiz--md">
                  <div className={styles.featureIcon}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16z"></path>
                      <path d="M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z"></path>
                      <path d="M12 2v2"></path>
                      <path d="M12 22v-2"></path>
                      <path d="m17 20.66-1-1.73"></path>
                      <path d="M11 10.27 7 3.34"></path>
                      <path d="m20.66 17-1.73-1"></path>
                      <path d="m3.34 7 1.73 1"></path>
                      <path d="M14 12h8"></path>
                      <path d="m2 12 3 3"></path>
                      <path d="m2 12 3-3"></path>
                    </svg>
                  </div>
                  <h3>Practical Focus</h3>
                  <p>Learn through hands-on examples connecting AI agents to ROS controllers.</p>
                </div>
              </div>
              <div className="col col--4">
                <div className="text--center padding-horiz--md">
                  <div className={styles.featureIcon}>
                    <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 8V4H8"></path>
                      <rect width="16" height="12" x="4" y="8" rx="2"></rect>
                      <path d="M2 14h2"></path>
                      <path d="M20 14h2"></path>
                      <path d="M15 13v2"></path>
                      <path d="M9 13v2"></path>
                    </svg>
                  </div>
                  <h3>Humanoid Robotics</h3>
                  <p>Specialized content for understanding the middleware that enables humanoid robot control.</p>
                </div>
              </div>
            </div>
          </div>
        </section>

        <section className={styles.modulesSection}>
          <div className="container">
            <div className="text--center padding-horiz--md">
              <h2 style={{color: '#1e293b', marginBottom: '2rem'}}>Learning Modules</h2>
              <div className="row">
                <div className="col col--3">
                  <Link to="/docs/module1" className={styles.moduleCard}>
                    <h3>Module 1</h3>
                    <p>The Robotic Nervous System (ROS 2)</p>
                  </Link>
                </div>
                <div className="col col--3">
                  <Link to="/docs/module2" className={styles.moduleCard}>
                    <h3>Module 2</h3>
                    <p>The Digital Twin (Gazebo & Unity)</p>
                  </Link>
                </div>
                <div className="col col--3">
                  <Link to="/docs/module3" className={styles.moduleCard}>
                    <h3>Module 3</h3>
                    <p>The AI-Robot Brain (NVIDIA Isaac™)</p>
                  </Link>
                </div>
                <div className="col col--3">
                  <Link to="/docs/module4" className={styles.moduleCard}>
                    <h3>Module 4</h3>
                    <p>Vision-Language-Action (VLA)</p>
                  </Link>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>
    </Layout>
  );
}