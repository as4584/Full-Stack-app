-- Portfolio Database Initialization Script
-- This script sets up the database schema for the portfolio application

-- Create extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create contacts table for storing contact form submissions
CREATE TABLE IF NOT EXISTS contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    subject VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    ip_address INET,
    user_agent TEXT,
    status VARCHAR(50) DEFAULT 'new' CHECK (status IN ('new', 'read', 'replied', 'archived')),
    replied_at TIMESTAMP WITH TIME ZONE,
    notes TEXT
);

-- Create index on email and created_at for efficient queries
CREATE INDEX IF NOT EXISTS idx_contacts_email ON contacts(email);
CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON contacts(created_at);
CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts(status);

-- Create projects table for dynamic project management
CREATE TABLE IF NOT EXISTS projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title VARCHAR(255) NOT NULL,
    description TEXT NOT NULL,
    long_description TEXT,
    image_url VARCHAR(500),
    case_study_url VARCHAR(500),
    technologies TEXT[], -- Array of technology names
    impact VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'draft')),
    featured BOOLEAN DEFAULT false,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on projects
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_featured ON projects(featured);
CREATE INDEX IF NOT EXISTS idx_projects_sort_order ON projects(sort_order);

-- Create testimonials table for dynamic testimonial management
CREATE TABLE IF NOT EXISTS testimonials (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_name VARCHAR(255) NOT NULL,
    position VARCHAR(255),
    company VARCHAR(255),
    text TEXT NOT NULL,
    rating INTEGER CHECK (rating >= 1 AND rating <= 5),
    status VARCHAR(50) DEFAULT 'active' CHECK (status IN ('active', 'archived', 'draft')),
    featured BOOLEAN DEFAULT false,
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create index on testimonials
CREATE INDEX IF NOT EXISTS idx_testimonials_status ON testimonials(status);
CREATE INDEX IF NOT EXISTS idx_testimonials_featured ON testimonials(featured);
CREATE INDEX IF NOT EXISTS idx_testimonials_rating ON testimonials(rating);

-- Create analytics table for basic site analytics
CREATE TABLE IF NOT EXISTS analytics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    event_type VARCHAR(100) NOT NULL, -- page_view, contact_form, project_click, etc.
    page_path VARCHAR(500),
    referrer VARCHAR(500),
    user_agent TEXT,
    ip_address INET,
    session_id VARCHAR(255),
    metadata JSONB, -- Additional event data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes on analytics
CREATE INDEX IF NOT EXISTS idx_analytics_event_type ON analytics(event_type);
CREATE INDEX IF NOT EXISTS idx_analytics_created_at ON analytics(created_at);
CREATE INDEX IF NOT EXISTS idx_analytics_page_path ON analytics(page_path);

-- Create function to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers to automatically update updated_at
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_testimonials_updated_at BEFORE UPDATE ON testimonials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert sample data
INSERT INTO projects (title, description, image_url, case_study_url, technologies, impact, featured, sort_order) VALUES
('AI Receptionist', 'Smart phone system that books appointments and handles customer inquiries 24/7', '/static/images/ai-receptionist.jpg', '/projects/ai-receptionist', ARRAY['FastAPI', 'OpenAI', 'Twilio', 'Python'], '90% reduction in missed calls, $2K+ monthly ROI', true, 1),
('Inventory Manager', 'Real-time inventory tracking system with automated reorder alerts', '/static/images/inventory-manager.jpg', '/projects/inventory-manager', ARRAY['Flask', 'PostgreSQL', 'Python', 'API'], 'Reduced inventory costs by 25%, eliminated stockouts', true, 2),
('SAP Integration', 'Custom API bridge connecting legacy systems to modern applications', '/static/images/sap-integration.jpg', '/projects/sap-integration', ARRAY['Python', 'SAP', 'REST API', 'Docker'], 'Automated 80% of manual data entry tasks', true, 3)
ON CONFLICT DO NOTHING;

INSERT INTO testimonials (client_name, position, company, text, rating, featured, sort_order) VALUES
('Maria Rodriguez', 'Owner', 'Bella Vista Salon', 'The AI receptionist has completely transformed our business. We never miss appointments anymore, and our customers love the 24/7 availability.', 5, true, 1),
('James Chen', 'Operations Manager', 'TechFlow Solutions', 'Lex delivered exactly what we needed - a robust API integration that just works. Professional, reliable, and great communication throughout.', 5, true, 2),
('Sarah Johnson', 'Restaurant Manager', 'Coastal Bistro', 'Our inventory system used to be a nightmare. Now everything is automated and we can focus on serving great food instead of counting supplies.', 5, true, 3)
ON CONFLICT DO NOTHING;

-- Grant permissions to the application user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO portfolio_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO portfolio_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO portfolio_user;