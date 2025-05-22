import React, { useState, useEffect } from 'react';
import {
  Container,
  TextField,
  Button,
  Typography,
  Paper,
  Box,
  CircularProgress,
  ToggleButtonGroup,
  ToggleButton,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Link,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import axios from 'axios';

function App() {
  const [queryMode, setQueryMode] = useState('nlp'); // 'nlp' or 'sql'
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [schema, setSchema] = useState(null);
  const [processedQuery, setProcessedQuery] = useState('');

  // Fetch schema on component mount
  useEffect(() => {
    fetchSchema();
  }, []);

  const fetchSchema = async () => {
    try {
      const response = await axios.get('http://localhost:8000/test-queries/tables');
      setSchema(response.data.results);
    } catch (err) {
      console.error('Error fetching schema:', err);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      let response;
      if (queryMode === 'nlp') {
        response = await axios.post('http://localhost:8000/query', { query });
      } else {
        // Force single line by replacing all newlines and extra spaces with a single space
        const singleLineQuery = query.replace(/[\r\n\s]+/g, ' ').trim();
        response = await axios.post('http://localhost:8000/execute-sql', { 
          query: singleLineQuery 
        });
      }
      setResults(response.data);
    } catch (err) {
      setError(err.response?.data?.detail || 'An error occurred while processing your query. Please try again.');
      console.error('Error:', err);
    } finally {
      setLoading(false);
    }
  };

  // Add this helper function at the top of your App.js file, outside the App component
  const formatDate = (dateString) => {
    try {
      return new Date(dateString).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      });
    } catch (e) {
      return dateString;
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom align="center">
          MoreFixes Query Interface
        </Typography>

        <Paper elevation={3} sx={{ p: 3, mb: 3 }}>
          <Box sx={{ mb: 2 }}>
            <ToggleButtonGroup
              value={queryMode}
              exclusive
              onChange={(e, newMode) => newMode && setQueryMode(newMode)}
              aria-label="query mode"
              fullWidth
            >
              <ToggleButton value="nlp" aria-label="natural language">
                Natural Language
              </ToggleButton>
              <ToggleButton value="sql" aria-label="sql">
                SQL Query
              </ToggleButton>
            </ToggleButtonGroup>
          </Box>

          {/* Schema View */}
          <Accordion sx={{ mb: 2 }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography>Database Schema</Typography>
            </AccordionSummary>
            <AccordionDetails>
              {schema ? (
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {JSON.stringify(schema, null, 2)}
                </pre>
              ) : (
                <Typography>Loading schema...</Typography>
              )}
            </AccordionDetails>
          </Accordion>

          <form onSubmit={handleSubmit}>
            <TextField
              fullWidth
              label={queryMode === 'nlp' ? "Enter your query in natural language" : "Enter your SQL query"}
              variant="outlined"
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                if (queryMode === 'sql') {
                  // Show processed query as helper text
                  const processed = e.target.value
                    .split(/\r?\n/)
                    .map(line => line.trim())
                    .filter(line => line)
                    .join(' ');
                  setProcessedQuery(processed);
                }
              }}
              multiline
              rows={3}
              sx={{ mb: 2 }}
              helperText={queryMode === 'sql' ? `Processed query: ${processedQuery}` : ''}
            />
            <Button
              type="submit"
              variant="contained"
              color="primary"
              fullWidth
              disabled={loading || !query.trim()}
            >
              {loading ? <CircularProgress size={24} /> : 'Execute Query'}
            </Button>
          </form>
        </Paper>

        {error && (
          <Paper elevation={3} sx={{ p: 2, mb: 2, bgcolor: '#ffebee' }}>
            <Typography color="error">{error}</Typography>
          </Paper>
        )}

        {results && (
          <Paper elevation={3} sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Results
            </Typography>
            
            {/* Debug section */}
            <Accordion sx={{ mb: 2 }}>
              <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                <Typography>Debug: Raw Response Data</Typography>
              </AccordionSummary>
              <AccordionDetails>
                <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                  {JSON.stringify(results, null, 2)}
                </pre>
              </AccordionDetails>
            </Accordion>

            {queryMode === 'sql' ? (
              // Raw JSON view for SQL queries
              <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {JSON.stringify(results, null, 2)}
              </pre>
            ) : (
              // Formatted view for NLP queries
              <Box>
                {results?.results?.length > 0 ? (
                  results.results.map((cve, index) => (
                    <Paper 
                      key={index}
                      elevation={1} 
                      sx={{ 
                        p: 2, 
                        mb: 2, 
                        backgroundColor: '#f8f9fa',
                        border: '1px solid #e9ecef'
                      }}
                    >
                      <Typography variant="h6" color="primary" gutterBottom>
                        {cve.cve_id || 'No CVE ID'}
                      </Typography>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body1" sx={{ mb: 1 }}>
                          {cve.description || 'No description available'}
                        </Typography>
                      </Box>

                      <Grid container spacing={2}>
                        <Grid item xs={12} sm={6}>
                          <Typography variant="subtitle2" color="textSecondary">
                            Published Date:
                          </Typography>
                          <Typography variant="body2" gutterBottom>
                            {cve.published_date ? formatDate(cve.published_date) : 'No date available'}
                          </Typography>
                        </Grid>

                        <Grid item xs={12} sm={6}>
                          <Typography variant="subtitle2" color="textSecondary">
                            Severity:
                          </Typography>
                          <Typography variant="body2">
                            {cve.severity ? `${cve.severity} (${cve.severity_score || 'N/A'})` : 'No severity information'}
                          </Typography>
                        </Grid>

                        {cve.repositories && (
                          <Grid item xs={12}>
                            <Typography variant="subtitle2" color="textSecondary">
                              Repositories:
                            </Typography>
                            <Typography variant="body2">
                              {cve.repositories}
                            </Typography>
                          </Grid>
                        )}

                        {cve.cwe_ids && (
                          <Grid item xs={12}>
                            <Typography variant="subtitle2" color="textSecondary">
                              CWE IDs:
                            </Typography>
                            <Typography variant="body2">
                              {cve.cwe_ids}
                            </Typography>
                          </Grid>
                        )}
                      </Grid>
                    </Paper>
                  ))
                ) : (
                  <Typography color="textSecondary">
                    No results found
                  </Typography>
                )}
              </Box>
            )}
          </Paper>
        )}
      </Box>
    </Container>
  );
}

export default App; 