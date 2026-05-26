import React, { useEffect, useState } from 'react';
import { 
  Search, 
  ShieldCheck, 
  TrendingDown, 
  Store, 
  Bell, 
  Sparkles, 
  Cpu, 
  ExternalLink,
  ChevronRight,
  Bookmark,
  Users
} from 'lucide-react';
import AuthPanel from './components/AuthPanel';
import Login from './pages/Login';
import Signup from './pages/Signup';

export default function App() {
  const [route, setRoute] = useState(() => window.location.hash || '#/');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('All');

  useEffect(() => {
    const onHashChange = () => setRoute(window.location.hash || '#/');
    window.addEventListener('hashchange', onHashChange);
    return () => window.removeEventListener('hashchange', onHashChange);
  }, []);

  const path = (route || '#/').replace(/^#/, '');
  if (path.startsWith('/login')) {
    return <Login />;
  }
  if (path.startsWith('/signup')) {
    return <Signup />;
  }

  const categories = ['All', 'Electronics', 'Phones', 'Laptops', 'Vehicles'];

  const mockListings = [
    {
      id: 1,
      title: "iPhone 15 Pro Max - 256GB",
      category: "Phones",
      price: "165,000 ETB",
      originalPrice: "180,000 ETB",
      discount: "8% Off",
      seller: "Abyssinia Tech",
      sellerScore: "9.8/10",
      sellerBadge: "Highly Trusted",
      source: "Jiji Ethiopia",
      link: "https://jiji.com.et",
      image: "📱"
    },
    {
      id: 2,
      title: "MacBook Pro M3 Max (16-inch)",
      category: "Laptops",
      price: "340,000 ETB",
      originalPrice: "355,000 ETB",
      discount: "4% Off",
      seller: "Shega Computers",
      sellerScore: "9.5/10",
      sellerBadge: "Top Seller",
      source: "Shega",
      link: "#",
      image: "💻"
    },
    {
      id: 3,
      title: "PlayStation 5 Console (Slim)",
      category: "Electronics",
      price: "68,000 ETB",
      originalPrice: "72,000 ETB",
      discount: "5% Off",
      seller: "Bole Electronics",
      sellerScore: "8.9/10",
      sellerBadge: "Verified",
      source: "Jiji Ethiopia",
      link: "#",
      image: "🎮"
    }
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      
      {/* Premium Header */}
      <header style={{
        padding: '1.5rem 2rem',
        borderBottom: '1px solid var(--border-glass)',
        background: 'rgba(7, 9, 14, 0.4)',
        backdropFilter: 'blur(12px)',
        position: 'sticky',
        top: 0,
        zIndex: 50
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <span style={{ fontSize: '1.8rem' }}>🇪🇹</span>
            <div>
              <h1 style={{ 
                fontFamily: 'Outfit', 
                fontSize: '1.4rem', 
                fontWeight: 800, 
                letterSpacing: '-0.5px',
                background: 'linear-gradient(to right, #ffffff, #9ca3af)',
                WebkitBackgroundClip: 'text',
                WebkitTextFillColor: 'transparent'
              }}>
                EthioCompare
              </h1>
              <p style={{ fontSize: '0.65rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '1px' }}>
                Smart Shopping Engine
              </p>
            </div>
          </div>
          
          <nav style={{ display: 'flex', gap: '1.5rem', alignItems: 'center' }}>
            <a href="#dashboard" style={{ color: 'var(--text-primary)', textDecoration: 'none', fontSize: '0.9rem', fontWeight: 500 }}>Dashboard</a>
            <a href="#scrapers" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.9rem' }}>Scrapers</a>
            <a href="#sellers" style={{ color: 'var(--text-secondary)', textDecoration: 'none', fontSize: '0.9rem' }}>Sellers</a>
            
            <button style={{
              background: 'var(--primary-glow)',
              color: 'var(--primary)',
              border: '1px solid hsla(var(--primary-hue), 95%, 60%, 0.3)',
              padding: '0.5rem 1rem',
              borderRadius: '99px',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              fontWeight: 600,
              fontSize: '0.85rem'
            }}>
              <Bell size={14} />
              Set Price Alert
            </button>
          </nav>
        </div>
      </header>

      {/* Main Content */}
      <main style={{ maxWidth: '1200px', margin: '0 auto', padding: '3rem 2rem', flex: 1, width: '100%' }}>
        
        {/* Hero Section */}
        <section style={{ textAlign: 'center', marginBottom: '3.5rem' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: '0.5rem',
            background: 'rgba(255,255,255,0.03)',
            border: '1px solid var(--border-glass)',
            padding: '0.4rem 1rem',
            borderRadius: '99px',
            fontSize: '0.8rem',
            color: 'var(--text-secondary)',
            marginBottom: '1.5rem'
          }}>
            <Sparkles size={14} style={{ color: 'var(--gold)' }} />
            <span>Real-time price comparisons across Addis Ababa & Ethiopia</span>
          </div>

          <h2 style={{
            fontFamily: 'Outfit',
            fontSize: '3rem',
            fontWeight: 800,
            lineHeight: 1.15,
            letterSpacing: '-1.5px',
            marginBottom: '1rem',
            background: 'linear-gradient(135deg, #ffffff 0%, #a5b4fc 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent'
          }}>
            Search Smarter.<br/>Save More Money.
          </h2>
          
          <p style={{
            color: 'var(--text-secondary)',
            maxWidth: '600px',
            margin: '0 auto 2.5rem auto',
            fontSize: '1.1rem',
            lineHeight: 1.6
          }}>
            Compare prices from Jiji, Shega, and top verified local retail outlets. 
            Track trusted merchant scoring before making your purchase.
          </p>

          {/* Premium Search Box */}
          <div style={{
            maxWidth: '680px',
            margin: '0 auto',
            position: 'relative'
          }}>
            <div style={{
              position: 'absolute',
              left: '1.25rem',
              top: '50%',
              transform: 'translateY(-50%)',
              color: 'var(--text-secondary)',
              display: 'flex',
              alignItems: 'center'
            }}>
              <Search size={22} />
            </div>
            
            <input 
              type="text" 
              placeholder="Search phones, laptops, electronics, vehicles..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '1.1rem 1.25rem 1.1rem 3.25rem',
                fontSize: '1.05rem',
                background: 'rgba(17, 24, 39, 0.65)',
                border: '1px solid var(--border-glass)',
                borderRadius: '16px',
                color: 'var(--text-primary)',
                outline: 'none',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)'
              }}
            />
          </div>

          {/* Category Tabs */}
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '0.75rem',
            marginTop: '1.5rem',
            flexWrap: 'wrap'
          }}>
            {categories.map((cat) => (
              <button
                key={cat}
                onClick={() => setSelectedCategory(cat)}
                style={{
                  background: selectedCategory === cat ? 'var(--primary)' : 'rgba(255,255,255,0.03)',
                  color: selectedCategory === cat ? '#ffffff' : 'var(--text-secondary)',
                  border: '1px solid',
                  borderColor: selectedCategory === cat ? 'var(--primary)' : 'var(--border-glass)',
                  padding: '0.45rem 1.2rem',
                  borderRadius: '99px',
                  cursor: 'pointer',
                  fontSize: '0.85rem',
                  fontWeight: 500
                }}
              >
                {cat}
              </button>
            ))}
          </div>
        </section>

        <AuthPanel />

        {/* Workspace Layout Structure Visualization */}
        <section style={{ display: 'grid', gridTemplateColumns: '1fr 2fr', gap: '2rem', marginTop: '4rem' }}>
          
          {/* Left Column: File Architecture & Quick Links */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ fontFamily: 'Outfit', fontSize: '1.1rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Cpu size={16} style={{ color: 'var(--primary)' }} />
                Workspace Architecture
              </h3>
              
              <div style={{ fontSize: '0.8rem', fontFamily: 'monospace', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                <div>📁 <strong style={{ color: 'var(--text-primary)' }}>ethiocompare</strong></div>
                <div style={{ paddingLeft: '1.25rem' }}>📁 <strong style={{ color: 'var(--text-primary)' }}>backend/</strong> <span style={{ color: 'var(--text-muted)' }}>(Django)</span></div>
                <div style={{ paddingLeft: '2.5rem' }}>📁 config/ <span style={{ color: 'var(--text-muted)' }}>(settings)</span></div>
                <div style={{ paddingLeft: '2.5rem' }}>📁 apps/ <span style={{ color: 'var(--text-muted)' }}>(modular)</span></div>
                <div style={{ paddingLeft: '3.75rem' }}>📂 users, products, sellers</div>
                <div style={{ paddingLeft: '3.75rem' }}>📂 listings, scraper, search</div>
                <div style={{ paddingLeft: '1.25rem' }}>📁 <strong style={{ color: 'var(--text-primary)' }}>frontend/</strong> <span style={{ color: 'var(--text-muted)' }}>(React)</span></div>
                <div style={{ paddingLeft: '2.5rem' }}>📂 pages, components, api</div>
              </div>
              
              <div style={{ 
                marginTop: '1.25rem', 
                padding: '0.75rem', 
                background: 'rgba(16, 185, 129, 0.05)', 
                border: '1px solid rgba(16, 185, 129, 0.2)',
                borderRadius: '8px',
                fontSize: '0.75rem',
                color: 'var(--accent)'
              }}>
                ✅ Django & React folders initialized successfully. All Django apps registered in settings.
              </div>
            </div>

            {/* Quick Status / Quick Actions */}
            <div className="glass-card" style={{ padding: '1.5rem' }}>
              <h3 style={{ fontFamily: 'Outfit', fontSize: '1.1rem', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Store size={16} style={{ color: 'var(--gold)' }} />
                Scraper Engines
              </h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Jiji Scraper</span>
                  <span style={{ color: 'var(--accent)', fontWeight: 600 }}>Active</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Shega Price Fetcher</span>
                  <span style={{ color: 'var(--accent)', fontWeight: 600 }}>Active</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.85rem' }}>
                  <span style={{ color: 'var(--text-secondary)' }}>Addis Mercado Engine</span>
                  <span style={{ color: 'var(--text-muted)' }}>Inactive</span>
                </div>
              </div>
            </div>
          </div>

          {/* Right Column: Simulated Live Listings */}
          <div>
            <h3 style={{ fontFamily: 'Outfit', fontSize: '1.25rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <TrendingDown size={18} style={{ color: 'var(--accent)' }} />
              Featured Deals Today
            </h3>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              {mockListings
                .filter(item => selectedCategory === 'All' || item.category === selectedCategory)
                .map((listing) => (
                  <div key={listing.id} className="glass-card" style={{ padding: '1.25rem', display: 'flex', gap: '1.25rem' }}>
                    <div style={{
                      width: '60px',
                      height: '60px',
                      background: 'rgba(255,255,255,0.03)',
                      borderRadius: '12px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontSize: '1.75rem',
                      border: '1px solid var(--border-glass)'
                    }}>
                      {listing.image}
                    </div>

                    <div style={{ flex: 1 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.25rem' }}>
                        <div>
                          <span style={{ fontSize: '0.75rem', color: 'var(--primary)', textTransform: 'uppercase', fontWeight: 600, tracking: '0.5px' }}>
                            {listing.category}
                          </span>
                          <h4 style={{ fontSize: '1.05rem', fontWeight: 600, color: 'var(--text-primary)', marginTop: '0.1rem' }}>
                            {listing.title}
                          </h4>
                        </div>
                        <span style={{
                          fontSize: '0.75rem',
                          background: 'rgba(255,255,255,0.05)',
                          border: '1px solid var(--border-glass)',
                          padding: '0.25rem 0.5rem',
                          borderRadius: '4px',
                          color: 'var(--text-secondary)'
                        }}>
                          {listing.source}
                        </span>
                      </div>

                      {/* Seller Score and Badging */}
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', margin: '0.6rem 0' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                          <Store size={12} style={{ color: 'var(--text-muted)' }} />
                          <span>{listing.seller}</span>
                        </div>
                        <div style={{ 
                          display: 'inline-flex', 
                          alignItems: 'center', 
                          gap: '0.25rem', 
                          fontSize: '0.75rem', 
                          color: 'var(--gold)',
                          background: 'rgba(234, 179, 8, 0.05)',
                          padding: '0.15rem 0.4rem',
                          borderRadius: '4px',
                          border: '1px solid rgba(234, 179, 8, 0.2)'
                        }}>
                          <ShieldCheck size={10} />
                          <span>Seller Score: {listing.sellerScore}</span>
                        </div>
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.75rem', borderTop: '1px solid rgba(255,255,255,0.04)', paddingTop: '0.75rem' }}>
                        <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.5rem' }}>
                          <span style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--accent)' }}>{listing.price}</span>
                          <span style={{ fontSize: '0.8rem', textDecoration: 'line-through', color: 'var(--text-muted)' }}>{listing.originalPrice}</span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--accent)', fontWeight: 600 }}>({listing.discount})</span>
                        </div>
                        
                        <a 
                          href={listing.link} 
                          target="_blank" 
                          rel="noreferrer" 
                          style={{
                            display: 'flex',
                            alignItems: 'center',
                            gap: '0.35rem',
                            fontSize: '0.8rem',
                            color: 'var(--primary)',
                            textDecoration: 'none',
                            fontWeight: 600
                          }}
                        >
                          View Listing
                          <ExternalLink size={12} />
                        </a>
                      </div>
                    </div>
                  </div>
                ))}
            </div>
          </div>

        </section>

      </main>

      {/* Footer */}
      <footer style={{
        padding: '2.5rem 2rem',
        borderTop: '1px solid var(--border-glass)',
        background: 'rgba(7, 9, 14, 0.8)',
        marginTop: '5rem',
        color: 'var(--text-muted)'
      }}>
        <div style={{
          maxWidth: '1200px',
          margin: '0 auto',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          fontSize: '0.85rem'
        }}>
          <div>
            <p>© {new Date().getFullYear()} EthioCompare Co. Built with Django & React.</p>
          </div>
          <div style={{ display: 'flex', gap: '1.5rem' }}>
            <a href="#privacy" style={{ color: 'var(--text-muted)', textDecoration: 'none' }}>Privacy Policy</a>
            <a href="#terms" style={{ color: 'var(--text-muted)', textDecoration: 'none' }}>Terms of Use</a>
          </div>
        </div>
      </footer>

    </div>
  );
}
