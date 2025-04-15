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

    // Article Modal Functionality
    const modal = document.getElementById('article-modal');
    const modalOverlay = document.querySelector('.modal-overlay');
    const modalClose = document.querySelector('.modal-close');
    const articleElements = document.querySelectorAll('.article-clickable');
    const readMoreLinks = document.querySelectorAll('.read-more-link');

    // Function to open the modal with an article
    async function openArticleModal(articleId) {
        try {
            // Fetch article data
            const response = await fetch(`/api/article/${articleId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch article');
            }
            
            const article = await response.json();
            
            // Populate modal with article data
            document.querySelector('.modal-title').textContent = article.title;
            document.querySelector('.modal-source').textContent = article.source;
            document.querySelector('.modal-date').textContent = article.published;
            
            // Set original link
            const originalLink = document.querySelector('.modal-original-link');
            originalLink.href = article.url;
            
            // Set author info if available
            const authorsElement = document.querySelector('.modal-authors');
            if (article.authors && article.authors.length > 0) {
                authorsElement.textContent = `By ${article.authors.join(', ')}`;
                authorsElement.style.display = 'block';
            } else {
                authorsElement.style.display = 'none';
            }
            
            // Set main image if available
            const imageContainer = document.querySelector('.modal-image-container');
            if (article.image) {
                imageContainer.innerHTML = `<img src="${article.image}" alt="${article.title}">`;
                imageContainer.style.display = 'block';
            } else if (article.images && article.images.length > 0) {
                imageContainer.innerHTML = `<img src="${article.images[0]}" alt="${article.title}">`;
                imageContainer.style.display = 'block';
            } else {
                imageContainer.style.display = 'none';
            }
            
            // Set article content
            const contentElement = document.querySelector('.modal-article-content');
            if (article.content_html) {
                contentElement.innerHTML = article.content_html;
            } else if (article.paragraphs && article.paragraphs.length > 0) {
                contentElement.innerHTML = article.paragraphs.map(p => `<p>${p}</p>`).join('');
            } else {
                contentElement.innerHTML = `<p>${article.summary}</p>`;
            }
            
            // Set keywords if available
            const keywordsElement = document.querySelector('.modal-keywords');
            if (article.keywords && article.keywords.length > 0) {
                keywordsElement.innerHTML = `
                    <h4>Related Topics</h4>
                    <div class="keyword-list">
                        ${article.keywords.map(keyword => 
                            `<a href="/?category=${encodeURIComponent(keyword)}" class="keyword-tag">${keyword}</a>`
                        ).join('')}
                    </div>
                `;
                keywordsElement.style.display = 'block';
            } else {
                keywordsElement.style.display = 'none';
            }
            
            // Set gallery images if available
            const galleryElement = document.querySelector('.modal-gallery');
            if (article.images && article.images.length > 1) {
                galleryElement.innerHTML = article.images.slice(1, 6).map(imgSrc => `
                    <div class="modal-gallery-image">
                        <img src="${imgSrc}" alt="Additional image for ${article.title}">
                    </div>
                `).join('');
                galleryElement.style.display = 'grid';
            } else {
                galleryElement.style.display = 'none';
            }
            
            // Show the modal
            modal.classList.add('active');
            document.body.classList.add('modal-open');
            
        } catch (error) {
            console.error('Error loading article:', error);
        }
    }
    
    // Function to close the modal
    function closeModal() {
        modal.classList.remove('active');
        document.body.classList.remove('modal-open');
    }
    
    // Event listener for article clicks
    articleElements.forEach(article => {
        article.addEventListener('click', () => {
            const articleId = article.dataset.articleId;
            openArticleModal(articleId);
        });
    });
    
    // Event listener for "Read more" links
    readMoreLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            e.stopPropagation(); // Prevent the click from reaching the parent article
            const articleId = link.dataset.articleId;
            openArticleModal(articleId);
        });
    });
    
    // Close modal when clicking the close button
    modalClose.addEventListener('click', closeModal);
    
    // Close modal when clicking outside the modal content
    modalOverlay.addEventListener('click', closeModal);
    
    // Prevent clicks inside the modal from closing it
    document.querySelector('.modal-container').addEventListener('click', e => {
        e.stopPropagation();
    });
    
    // Close modal with escape key
    document.addEventListener('keydown', e => {
        if (e.key === 'Escape' && modal.classList.contains('active')) {
            closeModal();
        }
    });
}); 