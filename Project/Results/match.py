import csv
import os
import re
import math
from collections import Counter

def read_csv(csv_file_path, text_column_index=1):
    """
    Read CSV file and extract the specified column.
    
    Args:
        csv_file_path (str): Path to the CSV file
        text_column_index (int): Index of the column containing text to compare (0-based)
        
    Returns:
        list: List of text entries from the specified column
    """
    entries = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader, None)  # Skip header row
        
        for row in csv_reader:
            if len(row) > text_column_index:
                entries.append(row[text_column_index])
    
    return entries

def read_csv_with_confidence(csv_file_path, text_column_index=1, confidence_column_index=2):
    """
    Read CSV file and extract the specified column along with confidence values.
    
    Args:
        csv_file_path (str): Path to the CSV file
        text_column_index (int): Index of the column containing text to compare (0-based)
        confidence_column_index (int): Index of the column containing confidence values
        
    Returns:
        tuple: (List of text entries, List of confidence values)
    """
    entries = []
    confidence_values = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        headers = next(csv_reader, None)  # Skip header row
        
        for row in csv_reader:
            if len(row) > max(text_column_index, confidence_column_index):
                entries.append(row[text_column_index])
                confidence_values.append(row[confidence_column_index])
    
    return entries, confidence_values

def preprocess_text(text):
    """
    Preprocess text by converting to lowercase, removing punctuation, and splitting into words.
    
    Args:
        text (str): Input text
        
    Returns:
        list: List of preprocessed words
    """
    # Convert to lowercase and remove punctuation
    text = text.lower()
    text = re.sub(r'[^\w\s]', '', text)
    
    # Split into words and remove stop words
    words = text.split()
    stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'if', 'because', 'as', 'what',
                  'when', 'where', 'how', 'which', 'who', 'this', 'that', 'to', 'of',
                  'in', 'for', 'on', 'by', 'with', 'about', 'is', 'are', 'was', 'were'}
    
    return [word for word in words if word not in stop_words]

def calculate_tf(words):
    """
    Calculate term frequency for a document.
    
    Args:
        words (list): List of words in the document
        
    Returns:
        dict: Term frequency dictionary
    """
    tf_dict = {}
    word_count = Counter(words)
    
    for word, count in word_count.items():
        tf_dict[word] = count / len(words)
    
    return tf_dict

def calculate_idf(documents):
    """
    Calculate inverse document frequency for a corpus.
    
    Args:
        documents (list): List of documents (each document is a list of words)
        
    Returns:
        dict: IDF dictionary
    """
    idf_dict = {}
    total_docs = len(documents)
    
    # Count document frequency for each word
    word_doc_count = {}
    for doc in documents:
        for word in set(doc):  # Use set to count each word only once per document
            word_doc_count[word] = word_doc_count.get(word, 0) + 1
    
    # Calculate IDF
    for word, doc_count in word_doc_count.items():
        idf_dict[word] = math.log(total_docs / doc_count)
    
    return idf_dict

def calculate_tfidf(tf, idf):
    """
    Calculate TF-IDF for a document.
    
    Args:
        tf (dict): Term frequency dictionary
        idf (dict): IDF dictionary
        
    Returns:
        dict: TF-IDF dictionary
    """
    tfidf = {}
    
    for word, tf_value in tf.items():
        tfidf[word] = tf_value * idf.get(word, 0)
    
    return tfidf

def cosine_similarity(vec1, vec2):
    """
    Calculate cosine similarity between two vectors.
    
    Args:
        vec1 (dict): First vector as a dictionary
        vec2 (dict): Second vector as a dictionary
        
    Returns:
        float: Cosine similarity value (0 to 1)
    """
    # Find common words
    common_words = set(vec1.keys()) & set(vec2.keys())
    
    # Calculate dot product
    dot_product = sum(vec1[word] * vec2[word] for word in common_words)
    
    # Calculate magnitudes
    mag1 = math.sqrt(sum(value ** 2 for value in vec1.values()))
    mag2 = math.sqrt(sum(value ** 2 for value in vec2.values()))
    
    # Handle zero magnitudes
    if mag1 == 0 or mag2 == 0:
        return 0
    
    return dot_product / (mag1 * mag2)

def find_matches_with_confidence(csv1_entries, csv2_entries, csv2_confidence, similarity_threshold=0.3):
    """
    Find matches between entries in two CSV files and track confidence levels.
    
    Args:
        csv1_entries (list): List of text entries from the first CSV
        csv2_entries (list): List of text entries from the second CSV
        csv2_confidence (list): List of confidence values from the second CSV
        similarity_threshold (float): Threshold for considering entries as matches
        
    Returns:
        tuple: (matched_pairs, matched_indices1, matched_indices2)
            matched_pairs: List of (idx1, idx2, confidence) tuples
            matched_indices1: Set of indices from csv1 that have matches
            matched_indices2: Set of indices from csv2 that have matches
    """
    # Preprocess all entries
    processed_entries1 = [preprocess_text(entry) for entry in csv1_entries]
    processed_entries2 = [preprocess_text(entry) for entry in csv2_entries]
    
    # Combine all documents for IDF calculation
    all_documents = processed_entries1 + processed_entries2
    idf = calculate_idf(all_documents)
    
    # Calculate TF-IDF for all entries
    tfidf1 = [calculate_tfidf(calculate_tf(doc), idf) for doc in processed_entries1]
    tfidf2 = [calculate_tfidf(calculate_tf(doc), idf) for doc in processed_entries2]
    
    # Find matches
    matched_indices1 = set()
    matched_indices2 = set()
    matched_pairs = []
    
    for i, vec1 in enumerate(tfidf1):
        best_match_idx = -1
        best_similarity = -1
        
        for j, vec2 in enumerate(tfidf2):
            similarity = cosine_similarity(vec1, vec2)
            
            if similarity > similarity_threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match_idx = j
        
        if best_match_idx != -1:
            matched_indices1.add(i)
            matched_indices2.add(best_match_idx)
            matched_pairs.append((i, best_match_idx, csv2_confidence[best_match_idx]))
    
    return matched_pairs, matched_indices1, matched_indices2

def parse_confidence_value(confidence_str):
    """
    Parse confidence value from a string, extracting confidence level and whether it's a definition.
    
    Args:
        confidence_str (str): Confidence string
        
    Returns:
        tuple: (confidence_level, is_definition)
    """
    confidence_str = confidence_str.lower()
    confidence_level = ""
    is_definition = False
    
    # Extract confidence level (first word)
    match = re.match(r'(\w+)', confidence_str)
    if match:
        confidence_level = match.group(1)
    
    # Check if it's a definition
    if 'definition' in confidence_str:
        is_definition = True
    
    return confidence_level, is_definition

def count_by_confidence(matched_pairs, csv2_confidence, matched_indices2, total_csv2):
    """
    Count true positives and false positives by confidence level and definition.
    
    Args:
        matched_pairs (list): List of (idx1, idx2, confidence) tuples
        csv2_confidence (list): List of confidence values from the second CSV
        matched_indices2 (set): Set of indices from csv2 that have matches
        total_csv2 (int): Total number of entries in csv2
        
    Returns:
        tuple: (true_positives_by_confidence, false_positives_by_confidence, 
               confidence_counts, definition_count, confidence_with_definition,
               true_positives_by_definition, false_positives_by_definition)
    """
    # Parse confidence values
    parsed_confidence = [parse_confidence_value(conf) for conf in csv2_confidence]
    
    # Count by confidence level
    true_positives_by_confidence = {'high': 0, 'medium': 0, 'low': 0}
    false_positives_by_confidence = {'high': 0, 'medium': 0, 'low': 0}
    confidence_counts = {'high': 0, 'medium': 0, 'low': 0}
    confidence_with_definition = {'high': 0, 'medium': 0, 'low': 0}
    definition_count = 0
    
    # Count for definitions
    true_positives_by_definition = 0
    false_positives_by_definition = 0
    
    # Count total by confidence
    for i, (level, is_def) in enumerate(parsed_confidence):
        if level in confidence_counts:
            confidence_counts[level] += 1
            
            if is_def:
                definition_count += 1
                confidence_with_definition[level] += 1
                
                # Count for definitions
                if i in matched_indices2:
                    true_positives_by_definition += 1
                else:
                    false_positives_by_definition += 1
                
            # Count true positives and false positives by confidence
            if i in matched_indices2:
                true_positives_by_confidence[level] += 1
            else:
                false_positives_by_confidence[level] += 1
    
    return (
        true_positives_by_confidence, 
        false_positives_by_confidence, 
        confidence_counts, 
        definition_count, 
        confidence_with_definition,
        true_positives_by_definition,
        false_positives_by_definition
    )

def generate_html_with_charts(match_results, output_path):
    """
    Generate HTML page with match results and charts.
    
    Args:
        match_results (dict): Dictionary containing match statistics and chart data
        output_path (str): Path to save the HTML file
    """
    # Prepare data for pie charts
    high_data = [match_results['true_positives_by_confidence']['high'], match_results['false_positives_by_confidence']['high']]
    medium_data = [match_results['true_positives_by_confidence']['medium'], match_results['false_positives_by_confidence']['medium']]
    low_data = [match_results['true_positives_by_confidence']['low'], match_results['false_positives_by_confidence']['low']]
    definition_data = [match_results['true_positives_by_definition'], match_results['false_positives_by_definition']]
    
    # Colors for the pie charts
    pie_colors = ['#7CCD7C', '#FF6C6C']  # Green for TP, Red for FP
    
    # Convert to JS format
    high_data_str = str(high_data)
    medium_data_str = str(medium_data)
    low_data_str = str(low_data)
    definition_data_str = str(definition_data)
    pie_colors_str = "['#7CCD7C', '#FF6C6C']"
    
    # Prepare data for the confidence bar charts
    conf_labels = ['High confidence', 'Medium confidence', 'Low confidence', 'Marked as definition']
    conf_values = [
        match_results['confidence_counts']['high'],
        match_results['confidence_counts']['medium'],
        match_results['confidence_counts']['low'],
        match_results['definition_count']
    ]
    conf_colors = ['#00cc44', '#ffcc00', '#ff3333', '#3366ff']  # Green, Yellow, Red, Blue
    conf_colors_str = "['" + "', '".join(conf_colors) + "']"
    
    # Prepare data for the confidence with definitions bar chart
    conf_def_labels = ['High confidence', 'Medium confidence', 'Low confidence']
    conf_def_values = [
        match_results['confidence_with_definition']['high'],
        match_results['confidence_with_definition']['medium'],
        match_results['confidence_with_definition']['low']
    ]
    conf_def_colors = conf_colors[:3]  # Use the same colors as the confidence chart
    conf_def_colors_str = "['" + "', '".join(conf_def_colors) + "']"
    
    # Data for confusion matrix
    true_positives = match_results['true_positives']
    false_positives = match_results['false_positives']
    false_negatives = match_results['false_negatives']
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSV Matching Results</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 0 auto;
            padding: 10px;
        }}
        h1 {{
            color: #333;
            margin-top: 10px;
            margin-bottom: 8px;
            font-size: 18px;
        }}
        .top-container {{
            display: flex;
            flex-direction: row;
            gap: 20px;
            margin-top: 20px;
            margin-bottom: 20px;
        }}
        .stats-container {{
            background-color: #f5f5f5;
            border-radius: 8px;
            padding: 20px;
            flex: 3;
        }}
        .overall-chart-container {{
            flex: 2;
            min-width: 250px;
            padding: 10px;
            background-color: #f5f5f5;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
        }}
        .stat-item {{
            margin-bottom: 15px;
        }}
        .stat-title {{
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .true-positive {{
            color: #00cc44;  /* Green */
        }}
        .false-negative {{
            color: #ff9900;  /* Orange */ 
        }}
        .false-positive {{
            color: #ff3333;  /* Red */
        }}
        .stat-description {{
            font-size: 14px;
            color: #666;
            margin-top: 3px;
        }}
        .chart-title {{
            color: #333;
            margin: 5px 0;
            font-size: 14px;
            text-align: center;
            font-weight: bold;
        }}
        .grid-container {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 25px;
            margin-top: 15px;
        }}
        .chart-wrapper {{
            width: 100%;
            margin-bottom: 20px;
        }}
        .chart-container {{
            width: 100%;
            height: 210px;
            margin-top: 5px;
        }}
        .full-width {{
            grid-column: 1 / -1;
        }}
        .chart-description {{
            text-align: center;
            margin: 3px 0;
            color: #555;
            font-size: 12px;
        }}
        /* Confusion Matrix Styles */
        .confusion-matrix {{
            border-collapse: collapse;
            width: 100%;
            font-size: 14px;
            margin-top: 5px;
            text-align: center;
        }}
        .confusion-matrix th {{
            background-color: #f0f0f0;
            padding: 8px;
            font-weight: bold;
        }}
        .confusion-matrix td {{
            padding: 10px;
            border: 1px solid #ddd;
        }}
        .confusion-matrix .empty-cell {{
            background-color: #f0f0f0;
        }}
        .confusion-matrix .header-cell {{
            background-color: #f0f0f0;
            font-weight: bold;
        }}
        .confusion-matrix .tp-cell {{
            background-color: rgba(0, 204, 68, 0.2);  /* Green */
        }}
        .confusion-matrix .fp-cell {{
            background-color: rgba(255, 51, 51, 0.2);  /* Red */
        }}
        .confusion-matrix .fn-cell {{
            background-color: rgba(255, 153, 0, 0.2);  /* Orange */
        }}
        .confusion-matrix .value {{
            font-size: 18px;
            font-weight: bold;
            display: block;
            margin-bottom: 5px;
        }}
        .confusion-matrix .label {{
            font-size: 12px;
            color: #666;
        }}
        .matrix-title {{
            margin-bottom: 5px;
            text-align: center;
            font-weight: bold;
            font-size: 14px;
        }}
    </style>
</head>
<body>
    <h1>CSV Matching Results</h1>
    
    <div class="top-container">
        <div class="stats-container">
            <div class="stat-item">
                <div class="stat-title true-positive">True Positives: {match_results['true_positives']}</div>
                <div class="stat-value">Rows from first CSV with a match in the second CSV: {match_results['true_positives']} of {match_results['total_csv1']} ({match_results['true_positive_percent']}%)</div>
                <div class="stat-description">These are rows from the first CSV that have similar content in the second CSV.</div>
            </div>
            
            <div class="stat-item">
                <div class="stat-title false-negative">False Negatives: {match_results['false_negatives']}</div>
                <div class="stat-value">Rows from first CSV with no match in the second CSV: {match_results['false_negatives']} of {match_results['total_csv1']} ({match_results['false_negative_percent']}%)</div>
                <div class="stat-description">These are rows from the first CSV that don't have similar content in the second CSV.</div>
            </div>
            
            <div class="stat-item">
                <div class="stat-title false-positive">False Positives: {match_results['false_positives']}</div>
                <div class="stat-value">Rows from second CSV with no match in the first CSV: {match_results['false_positives']} of {match_results['total_csv2']} ({match_results['false_positive_percent']}%)</div>
                <div class="stat-description">These are rows from the second CSV that don't have similar content in the first CSV.</div>
            </div>
        </div>
        
        <div class="overall-chart-container">
            <div class="matrix-title">Confusion Matrix</div>
            <table class="confusion-matrix">
                <tr>
                    <th class="empty-cell"></th>
                    <th>Predicted Match</th>
                    <th>Predicted No Match</th>
                </tr>
                <tr>
                    <td class="header-cell">Actual Match</td>
                    <td class="tp-cell">
                        <span class="value">{true_positives}</span>
                        <span class="label">True Positives</span>
                    </td>
                    <td class="fn-cell">
                        <span class="value">{false_negatives}</span>
                        <span class="label">False Negatives</span>
                    </td>
                </tr>
                <tr>
                    <td class="header-cell">Actual No Match</td>
                    <td class="fp-cell">
                        <span class="value">{false_positives}</span>
                        <span class="label">False Positives</span>
                    </td>
                    <td class="empty-cell">
                        <span class="value">-</span>
                        <span class="label">N/A</span>
                    </td>
                </tr>
            </table>
        </div>
    </div>
    
    <div class="grid-container">
        <!-- Pie charts by confidence level -->
        <div class="chart-wrapper">
            <div class="chart-title">High Confidence Results</div>
            <div class="chart-container">
                <canvas id="highConfChart"></canvas>
            </div>
        </div>
        
        <div class="chart-wrapper">
            <div class="chart-title">Medium Confidence Results</div>
            <div class="chart-container">
                <canvas id="mediumConfChart"></canvas>
            </div>
        </div>
        
        <div class="chart-wrapper">
            <div class="chart-title">Low Confidence Results</div>
            <div class="chart-container">
                <canvas id="lowConfChart"></canvas>
            </div>
        </div>
        
        <div class="chart-wrapper">
            <div class="chart-title">Definition Rows Results</div>
            <div class="chart-container">
                <canvas id="definitionChart"></canvas>
            </div>
        </div>
        
        <!-- Bar charts -->
        <div class="chart-wrapper">
            <div class="chart-title">Distribution by confidence and definitions</div>
            <div class="chart-description">Number of excerpts by confidence level and definitions</div>
            <div class="chart-container">
                <canvas id="confidenceChart"></canvas>
            </div>
        </div>
        
        <div class="chart-wrapper">
            <div class="chart-title">Definitions by confidence level</div>
            <div class="chart-description">Rows with each confidence level marked as definitions</div>
            <div class="chart-container">
                <canvas id="confDefChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        // PIE CHART - High Confidence
        const highCtx = document.getElementById('highConfChart').getContext('2d');
        new Chart(highCtx, {{
            type: 'pie',
            data: {{
                labels: ['Useful (High)', 'Useless (High)'],
                datasets: [{{
                    data: {high_data_str},
                    backgroundColor: {pie_colors_str},
                    borderColor: 'white',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                layout: {{
                    padding: {{
                        top: 10,
                        bottom: 10
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            font: {{
                                size: 10
                            }},
                            boxWidth: 10,
                            padding: 8
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${{label}}: ${{value}} (${{percentage}}%)`;
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // PIE CHART - Medium Confidence
        const mediumCtx = document.getElementById('mediumConfChart').getContext('2d');
        new Chart(mediumCtx, {{
            type: 'pie',
            data: {{
                labels: ['Useful (Medium)', 'Useless (Medium)'],
                datasets: [{{
                    data: {medium_data_str},
                    backgroundColor: {pie_colors_str},
                    borderColor: 'white',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                layout: {{
                    padding: {{
                        top: 10,
                        bottom: 10
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            font: {{
                                size: 10
                            }},
                            boxWidth: 10,
                            padding: 8
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${{label}}: ${{value}} (${{percentage}}%)`;
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // PIE CHART - Low Confidence
        const lowCtx = document.getElementById('lowConfChart').getContext('2d');
        new Chart(lowCtx, {{
            type: 'pie',
            data: {{
                labels: ['Useful (Low)', 'Useless (Low)'],
                datasets: [{{
                    data: {low_data_str},
                    backgroundColor: {pie_colors_str},
                    borderColor: 'white',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                layout: {{
                    padding: {{
                        top: 10,
                        bottom: 10
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            font: {{
                                size: 10
                            }},
                            boxWidth: 10,
                            padding: 8
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${{label}}: ${{value}} (${{percentage}}%)`;
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // PIE CHART - Definitions
        const defCtx = document.getElementById('definitionChart').getContext('2d');
        new Chart(defCtx, {{
            type: 'pie',
            data: {{
                labels: ['Useful (Definition)', 'Useless (Definition)'],
                datasets: [{{
                    data: {definition_data_str},
                    backgroundColor: {pie_colors_str},
                    borderColor: 'white',
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                layout: {{
                    padding: {{
                        top: 10,
                        bottom: 10
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'right',
                        labels: {{
                            font: {{
                                size: 10
                            }},
                            boxWidth: 10,
                            padding: 8
                        }}
                    }},
                    tooltip: {{
                        callbacks: {{
                            label: function(context) {{
                                const label = context.label || '';
                                const value = context.raw || 0;
                                const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${{label}}: ${{value}} (${{percentage}}%)`;
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // BAR CHART - Confidence and Definitions
        const confLabels = {str(conf_labels)};
        const confValues = {str(conf_values)};
        const confColors = {conf_colors_str};
        
        const confCtx = document.getElementById('confidenceChart').getContext('2d');
        new Chart(confCtx, {{
            type: 'bar',
            data: {{
                labels: confLabels,
                datasets: [{{
                    label: 'Number of excerpts',
                    data: confValues,
                    backgroundColor: confColors,
                    borderColor: confColors,
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                layout: {{
                    padding: {{
                        top: 5,
                        bottom: 5
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 20,
                        ticks: {{
                            precision: 0,
                            font: {{
                                size: 9
                            }}
                        }},
                        title: {{
                            display: false
                        }}
                    }},
                    x: {{
                        ticks: {{
                            font: {{
                                size: 8
                            }}
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    tooltip: {{
                        enabled: true
                    }}
                }}
            }}
        }});
        
        // BAR CHART - Definitions by Confidence Level
        const confDefLabels = {str(conf_def_labels)};
        const confDefValues = {str(conf_def_values)};
        const confDefColors = {conf_def_colors_str};
        
        const confDefCtx = document.getElementById('confDefChart').getContext('2d');
        new Chart(confDefCtx, {{
            type: 'bar',
            data: {{
                labels: confDefLabels,
                datasets: [{{
                    label: 'Rows with definitions',
                    data: confDefValues,
                    backgroundColor: confDefColors,
                    borderColor: confDefColors,
                    borderWidth: 1
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                layout: {{
                    padding: {{
                        top: 5,
                        bottom: 5
                    }}
                }},
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 10,
                        ticks: {{
                            precision: 0,
                            font: {{
                                size: 9
                            }}
                        }},
                        title: {{
                            display: false
                        }}
                    }},
                    x: {{
                        ticks: {{
                            font: {{
                                size: 8
                            }}
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        display: false
                    }},
                    tooltip: {{
                        enabled: true
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>
"""
    
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(html_content)

def main(csv1_path, csv2_path, output_dir='output', similarity_threshold=0.3):
    """
    Main function to compare two CSV files and generate match results with charts.
    
    Args:
        csv1_path (str): Path to the first CSV file
        csv2_path (str): Path to the second CSV file
        output_dir (str): Directory to save output files
        similarity_threshold (float): Threshold for considering entries as matches
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Read CSV files
    csv1_entries = read_csv(csv1_path, text_column_index=1)  # Details column
    csv2_entries, csv2_confidence = read_csv_with_confidence(csv2_path, text_column_index=1, confidence_column_index=2)  # Extract column
    
    # Find matches
    matched_pairs, matched_indices1, matched_indices2 = find_matches_with_confidence(
        csv1_entries, csv2_entries, csv2_confidence, similarity_threshold
    )
    
    # Count by confidence
    (
        true_positives_by_confidence,
        false_positives_by_confidence,
        confidence_counts,
        definition_count,
        confidence_with_definition,
        true_positives_by_definition,
        false_positives_by_definition
    ) = count_by_confidence(
        matched_pairs, csv2_confidence, matched_indices2, len(csv2_entries)
    )
    
    # Calculate statistics
    total_csv1 = len(csv1_entries)
    total_csv2 = len(csv2_entries)
    true_positives = len(matched_indices1)
    false_negatives = total_csv1 - true_positives
    false_positives = total_csv2 - len(matched_indices2)
    
    # Calculate percentages
    true_positive_percent = round((true_positives / total_csv1) * 100, 1) if total_csv1 > 0 else 0
    false_negative_percent = round((false_negatives / total_csv1) * 100, 1) if total_csv1 > 0 else 0
    false_positive_percent = round((false_positives / total_csv2) * 100, 1) if total_csv2 > 0 else 0
    
    # Prepare results
    match_results = {
        'total_csv1': total_csv1,
        'total_csv2': total_csv2,
        'true_positives': true_positives,
        'false_negatives': false_negatives,
        'false_positives': false_positives,
        'true_positive_percent': true_positive_percent,
        'false_negative_percent': false_negative_percent,
        'false_positive_percent': false_positive_percent,
        'true_positives_by_confidence': true_positives_by_confidence,
        'false_positives_by_confidence': false_positives_by_confidence,
        'confidence_counts': confidence_counts,
        'definition_count': definition_count,
        'confidence_with_definition': confidence_with_definition,
        'true_positives_by_definition': true_positives_by_definition,
        'false_positives_by_definition': false_positives_by_definition
    }
    
    # Generate HTML
    html_path = os.path.join(output_dir, 'match visualization.html')
    generate_html_with_charts(match_results, html_path)
    
    print(f"CSV 1 total rows: {total_csv1}")
    print(f"CSV 2 total rows: {total_csv2}")
    print(f"True positives (rows from CSV 1 with matches in CSV 2): {true_positives} ({true_positive_percent}%)")
    print(f"False negatives (rows from CSV 1 with no matches in CSV 2): {false_negatives} ({false_negative_percent}%)")
    print(f"False positives (rows from CSV 2 with no matches in CSV 1): {false_positives} ({false_positive_percent}%)")
    print(f"Results saved to: {html_path}")

if __name__ == "__main__":
    import sys
    
    csv1_path = "match.csv"
    csv2_path = "matchAI.csv"
    
    if len(sys.argv) > 2:
        csv1_path = sys.argv[1]
        csv2_path = sys.argv[2]
    
    main(csv1_path, csv2_path)
