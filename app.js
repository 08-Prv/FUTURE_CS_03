let allFiles = [];

window.onload = () => {
  fetchFiles();
};

function fetchFiles() {
  fetch('/files')
    .then(res => res.json())
    .then(data => {
      allFiles = data.files; // allFiles are original filenames without UUID prefix
      displayFiles(allFiles);
    });
}

function displayFiles(fileList) {
  const container = document.getElementById('searchResults');
  container.innerHTML = '';

  if (!fileList.length) {
    container.innerHTML = '<p>No files found.</p>';
    return;
  }

  fileList.forEach(file => {
    const div = document.createElement('div');
    div.className = 'file-item';
    div.innerHTML = `
      <strong>${file}</strong>
      <button onclick="downloadFile('${file}')">Download</button>
      <button onclick="deleteFile('${file}')">Delete</button>
      <button onclick="modifyFile('${file}')">Modify</button>
    `;
    container.appendChild(div);
  });
}

document.getElementById('searchBox').addEventListener('input', function () {
  const query = this.value.toLowerCase();
  const filtered = allFiles.filter(f => f.toLowerCase().includes(query));
  displayFiles(filtered);
});

document.getElementById('uploadForm').addEventListener('submit', function (e) {
  e.preventDefault();

  const fileInput = document.getElementById('uploadFile');
  const file = fileInput.files[0];
  if (!file) return alert("Please select a file to upload.");

  const formData = new FormData();
  formData.append('file', file);

  fetch('/upload', {
    method: 'POST',
    body: formData
  })
    .then(res => res.json())
    .then(data => {
      alert(data.message || data.error);
      fileInput.value = '';
      fetchFiles();
    });
});

function downloadFile(filename) {
  // Filename is original name, backend maps it internally
  window.location.href = '/download/' + encodeURIComponent(filename);
}

function deleteFile(filename) {
  if (!confirm(`Are you sure you want to delete "${filename}"?`)) return;

  fetch('/delete/' + encodeURIComponent(filename), {
    method: 'DELETE'
  })
    .then(res => res.json())
    .then(data => {
      alert(data.message || data.error);
      fetchFiles();
    });
}

function modifyFile(filename) {
  const fileInput = document.createElement('input');
  fileInput.type = 'file';
  fileInput.accept = '*/*';

  fileInput.onchange = function () {
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);

    fetch('/modify/' + encodeURIComponent(filename), {
      method: 'PUT',
      body: formData
    })
      .then(res => res.json())
      .then(data => {
        alert(data.message || data.error);
        fetchFiles();
      });
  };

  fileInput.click();
}
