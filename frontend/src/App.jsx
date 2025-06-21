import { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import Footer from './Footer';

const API_BASE_URL = '/api';

function App() {
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileData, setFileData] = useState(null);
  const [error, setError] = useState('');
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'ascending' });

  useEffect(() => {
    axios.get(`${API_BASE_URL}/files`)
      .then(response => {
        setFiles(response.data);
      })
      .catch(error => {
        console.error('Error fetching files:', error);
        setError('Could not fetch files from the server. Is the backend running?');
      });
  }, []);

  const handleFileSelect = (file) => {
    setSelectedFile(file);
    setFileData(null); // Reset previous data
    setSortConfig({ key: null, direction: 'ascending' });
    axios.get(`${API_BASE_URL}/file/${file}`)
      .then(response => {
        setFileData(response.data);
      })
      .catch(error => {
        console.error(`Error fetching data for ${file}:`, error);
        setError(`Could not fetch data for ${file}.`);
      });
  };

  const sortedData = () => {
    if (!fileData || !fileData.data) return [];
    let sortableItems = [...fileData.data];
    if (sortConfig.key !== null) {
      sortableItems.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableItems;
  };

  const requestSort = (key) => {
    let direction = 'ascending';
    if (sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };

  const getSortDirectionSymbol = (key) => {
    if (sortConfig.key === key) {
      return sortConfig.direction === 'ascending' ? ' ▲' : ' ▼';
    }
    return '';
  };


  return (
    <div className="App">
      <header className="App-header">
        <h1>Zacks Excel Data Viewer</h1>
      </header>
      <nav>
        <h2>Available Files</h2>
        {files.length > 0 ? (
          <ul>
            {files.map(file => (
              <li key={file}>
                <button onClick={() => handleFileSelect(file)} disabled={selectedFile === file}>
                  {file}
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p>{error ? error : 'Loading files...'}</p>
        )}
      </nav>
      <main>
        {selectedFile && <h2>Data for {selectedFile}</h2>}
        {fileData ? (
          <table>
            <thead>
              <tr>
                {fileData.headers.map(header => (
                  <th key={header} onClick={() => requestSort(header)}>
                    {header.replace(/_/g, ' ')}
                    {getSortDirectionSymbol(header)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {sortedData().map((row, index) => (
                <tr key={index}>
                  {fileData.headers.map(header => (
                    <td key={header}>{row[header]}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          selectedFile && <p>Loading data...</p>
        )}
      </main>
      <Footer />
    </div>
  );
}

export default App;
