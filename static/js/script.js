// Wait for DOM to load
document.addEventListener('DOMContentLoaded', () => {
    // Add current date to the page
    const dateElement = document.querySelector('.date');
    if (dateElement) {
        const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
        const currentDate = new Date().toLocaleDateString('en-US', options);
        dateElement.textContent = currentDate;
    }
    
    // Add current year to footer
    const footerYear = document.querySelector('footer p');
    if (footerYear) {
        const yearString = footerYear.textContent;
        footerYear.textContent = yearString.replace('{{ current_year }}', new Date().getFullYear());
    }
    
    // Add smooth scrolling to internal links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            if (targetId !== '#') {
                document.querySelector(targetId).scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
}); 