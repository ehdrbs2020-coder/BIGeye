document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('excel-file');
    const fileDropArea = document.getElementById('file-drop-area');
    const fileInfo = document.getElementById('file-info');
    const fileNameDisplay = document.getElementById('file-name');
    
    const keywordInput = document.getElementById('keyword-input');
    const addKeywordBtn = document.getElementById('add-keyword-btn');
    const keywordTags = document.getElementById('keyword-tags');
    const keywordExcelInput = document.getElementById('keyword-excel-file');
    
    const startBtn = document.getElementById('start-btn');
    const loadingOverlay = document.getElementById('loading-overlay');

    let selectedFile = null;
    // 초기 기본 키워드 세팅
    let keywords = new Set(['최고', '다이어트', '체중감량', '1등', '의료기기', '성인']);

    const renderKeywords = () => {
        keywordTags.innerHTML = '';
        keywords.forEach(kw => {
            const tag = document.createElement('div');
            tag.className = 'tag';
            tag.innerHTML = `<span>${kw}</span> <span class="tag-close" data-kw="${kw}">✕</span>`;
            keywordTags.appendChild(tag);
        });
        checkFormValidity();
    };
    renderKeywords();

    keywordTags.addEventListener('click', (e) => {
        if (e.target.classList.contains('tag-close')) {
            keywords.delete(e.target.getAttribute('data-kw'));
            renderKeywords();
        }
    });

    const addKeyword = () => {
        const val = keywordInput.value.trim();
        if (val) {
            // 콤마로 분리해서 여러개 동시 추가 가능하도록
            val.split(',').forEach(k => {
                const cleanK = k.trim();
                if(cleanK) keywords.add(cleanK);
            });
            keywordInput.value = '';
            renderKeywords();
        }
    };

    addKeywordBtn.addEventListener('click', addKeyword);
    keywordInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') addKeyword();
    });

    // Keyword Excel Upload
    keywordExcelInput.addEventListener('change', async function() {
        if (this.files.length > 0) {
            const file = this.files[0];
            if (file.name.endsWith('.xlsx')) {
                const formData = new FormData();
                formData.append('file', file);
                
                try {
                    const response = await fetch('/api/extract-keywords', {
                        method: 'POST',
                        body: formData
                    });
                    if (!response.ok) throw new Error('엑셀 파싱 실패');
                    const data = await response.json();
                    data.keywords.forEach(kw => {
                        const cleanK = kw.trim();
                        if(cleanK) keywords.add(cleanK);
                    });
                    renderKeywords();
                    // input 초기화
                    this.value = '';
                } catch (e) {
                    alert('키워드 엑셀을 읽는 중 오류가 발생했습니다.');
                }
            } else {
                alert('엑셀 파일(.xlsx)만 업로드 가능합니다.');
            }
        }
    });

    // File Drag & Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => fileDropArea.classList.add('dragover'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, () => fileDropArea.classList.remove('dragover'), false);
    });

    fileDropArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        handleFiles(dt.files);
    });

    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (file.name.endsWith('.xlsx')) {
                selectedFile = file;
                fileNameDisplay.textContent = file.name;
                fileInfo.classList.remove('hidden');
                checkFormValidity();
            } else {
                alert('엑셀 파일(.xlsx)만 업로드 가능합니다.');
            }
        }
    }

    function checkFormValidity() {
        if (selectedFile && keywords.size > 0) {
            startBtn.disabled = false;
        } else {
            startBtn.disabled = true;
        }
    }

    const resultsSection = document.getElementById('results-section');
    const summaryTotal = document.getElementById('summary-total');
    const summaryWarning = document.getElementById('summary-warning');
    const summaryOk = document.getElementById('summary-ok');
    const downloadBtn = document.getElementById('download-btn');

    let currentExcelBase64 = null;
    let currentFilename = null;

    // Download Logic
    downloadBtn.addEventListener('click', () => {
        if (!currentExcelBase64 || !currentFilename) return;
        
        const byteCharacters = atob(currentExcelBase64);
        const byteNumbers = new Array(byteCharacters.length);
        for (let i = 0; i < byteCharacters.length; i++) {
            byteNumbers[i] = byteCharacters.charCodeAt(i);
        }
        const byteArray = new Uint8Array(byteNumbers);
        const blob = new Blob([byteArray], {type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'});
        
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = currentFilename;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
    });

    // Submit Logic
    startBtn.addEventListener('click', async () => {
        if (!selectedFile || keywords.size === 0) return;

        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('keywords', Array.from(keywords).join(','));

        loadingOverlay.classList.remove('hidden');
        resultsSection.classList.add('hidden'); // Reset UI

        try {
            const response = await fetch('/api/inspect', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || '서버 오류가 발생했습니다.');
            }

            const data = await response.json();
            
            // 데이터 렌더링
            summaryTotal.textContent = data.total_count + '건';
            summaryWarning.textContent = data.warning_count + '건';
            summaryOk.textContent = data.ok_count + '건';
            
            // 다운로드 변수 세팅
            currentExcelBase64 = data.file_base64;
            currentFilename = data.filename;
            
            // 결과 섹션 표시
            resultsSection.classList.remove('hidden');

        } catch (error) {
            alert(error.message);
        } finally {
            loadingOverlay.classList.add('hidden');
        }
    });
});
