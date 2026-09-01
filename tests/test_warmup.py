import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.html_processor import HTMLProcessorService
from app.database import engine, Base, SessionLocal
from app.models.schema import SeedAccount, WarmupLog, WarmupMetric

def test_database_models():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Test Account Creation
    acc = SeedAccount(
        email="test_seed@example.com",
        password="secretpassword",
        imap_host="imap.example.com",
        smtp_host="smtp.example.com"
    )
    db.add(acc)
    db.commit()
    db.refresh(acc)
    
    assert acc.id is not None
    assert acc.email == "test_seed@example.com"
    assert acc.total_opened == 0

    # Cleanup
    db.delete(acc)
    db.commit()
    db.close()
    print("[PASS] Database models test passed!")

def test_html_cta_extraction():
    processor = HTMLProcessorService()
    sample_html = """
    <html>
        <body>
            <p>Hi there! Thanks for joining us.</p>
            <img src="http://example.com/track/pixel.png?id=123" width="1" height="1" />
            <a href="https://example.com/confirm-account?token=xyz">Click Here to Confirm</a>
            <a href="https://example.com/unsubscribe">Unsubscribe</a>
        </body>
    </html>
    """
    
    cta_links = processor.extract_cta_links(sample_html)
    assert "https://example.com/confirm-account?token=xyz" in cta_links
    assert "https://example.com/unsubscribe" not in cta_links
    print("[PASS] CTA link extraction test passed!")

if __name__ == "__main__":
    test_database_models()
    test_html_cta_extraction()
    print("All unit tests completed successfully!")
