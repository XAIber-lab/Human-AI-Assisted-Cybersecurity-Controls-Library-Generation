import csv
import os
import re

def find_column_index(headers, column_name):
    """
    Find the index of a column name in a case-insensitive manner.
    
    Args:
        headers (list): List of header names
        column_name (str): Column name to find
        
    Returns:
        int: Index of the column
    
    Raises:
        ValueError: If the column is not found
    """
    for i, header in enumerate(headers):
        if header.lower() == column_name.lower():
            return i
    raise ValueError(f"Column not found: {column_name}")

def process_csv(csv_file_path):
    """
    Process a CSV file to analyze first proposals, confidence values, and definitions.
    Distinguishes between NIST Cybersecurity Framework and NIST Privacy Framework.
    
    Args:
        csv_file_path (str): Path to the CSV file
        
    Returns:
        dict: A dictionary containing total row count, prefix counts for both frameworks,
              confidence counts, definition count, and confidence with definition counts
    """
    # Initialize data structures
    total_rows = 0
    cyber_prefix_counts = {}
    privacy_prefix_counts = {}
    confidence_counts = {'high': 0, 'medium': 0, 'low': 0}
    definition_count = 0
    confidence_with_definition = {'high': 0, 'medium': 0, 'low': 0}
    
    # Read the CSV file
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        # Read the first line to get headers
        header_line = file.readline().strip()
        headers = header_line.split('@')
        
        # Find the indexes of required columns (case-insensitive)
        try:
            first_proposal_index = find_column_index(headers, 'first proposal')
            confidence_index = find_column_index(headers, 'confidence')
            definitions_index = find_column_index(headers, 'definitions')
        except ValueError as e:
            raise ValueError(f"Required column not found in the CSV file: {e}")
        
        # Process each line
        for line in file:
            if line.strip():  # Skip empty lines
                total_rows += 1
                fields = line.strip().split('@')
                
                # Ensure there are enough fields
                if len(fields) > max(first_proposal_index, confidence_index, definitions_index):
                    # Process first proposal
                    first_proposal = fields[first_proposal_index]
                    
                    # Check if the proposal contains a framework reference code
                    framework_code = None
                    is_privacy_framework = False
                    
                    # Extract framework code from the first proposal
                    # Look for patterns like RS.CO-02 (Cybersecurity) or PR.PT-P3 (Privacy)
                    parts = first_proposal.split(';')
                    for part in parts:
                        part = part.strip()
                        # Check for Cybersecurity Framework pattern (XX.XX-00)
                        if re.search(r'[A-Z]{2}\.[A-Z]{2}-\d{2}', part):
                            framework_code = part[:2]  # First two letters = function prefix
                            is_privacy_framework = False
                            break
                        # Check for Privacy Framework pattern (XX.XX-P0)
                        elif re.search(r'[A-Z]{2}\.[A-Z]{2}-P\d', part):
                            framework_code = part[:2] + "-P"  # Add "-P" to distinguish from cyber
                            is_privacy_framework = True
                            break
                    
                    if framework_code:
                        if is_privacy_framework:
                            privacy_prefix_counts[framework_code] = privacy_prefix_counts.get(framework_code, 0) + 1
                        else:
                            cyber_prefix_counts[framework_code] = cyber_prefix_counts.get(framework_code, 0) + 1
                    
                    # Process confidence value
                    confidence = fields[confidence_index].lower()
                    if 'high' in confidence:
                        confidence_counts['high'] += 1
                    elif 'medium' in confidence:
                        confidence_counts['medium'] += 1
                    elif 'low' in confidence:
                        confidence_counts['low'] += 1
                    
                    # Process definitions
                    definitions = fields[definitions_index] if definitions_index < len(fields) else ""
                    has_definition = 'definition' in definitions.lower()
                    
                    if has_definition:
                        definition_count += 1
                        
                        # Count confidence values with definitions
                        if 'high' in confidence:
                            confidence_with_definition['high'] += 1
                        elif 'medium' in confidence:
                            confidence_with_definition['medium'] += 1
                        elif 'low' in confidence:
                            confidence_with_definition['low'] += 1
    
    # Map prefixes to full names for Cybersecurity Framework
    cyber_prefix_mapping = {
        'GV': 'GOVERN',
        'ID': 'IDENTIFY',
        'PR': 'PROTECT',
        'DE': 'DETECT',
        'RS': 'RESPOND',
        'RC': 'RECOVER'
    }
    
    # Map prefixes to full names for Privacy Framework
    privacy_prefix_mapping = {
        'ID-P': 'IDENTIFY-P',
        'GV-P': 'GOVERN-P',
        'CT-P': 'CONTROL-P',
        'CM-P': 'COMMUNICATE-P',
        'PR-P': 'PROTECT-P'
    }
    
    # Replace prefix keys with full names for Cybersecurity Framework
    cyber_named_counts = {}
    for prefix, count in cyber_prefix_counts.items():
        full_name = cyber_prefix_mapping.get(prefix, prefix)
        cyber_named_counts[full_name] = count
    
    # Replace prefix keys with full names for Privacy Framework
    privacy_named_counts = {}
    for prefix, count in privacy_prefix_counts.items():
        full_name = privacy_prefix_mapping.get(prefix, prefix)
        privacy_named_counts[full_name] = count
    
    return {
        'total_rows': total_rows,
        'cyber_prefix_counts': cyber_named_counts,
        'privacy_prefix_counts': privacy_named_counts,
        'confidence_counts': confidence_counts,
        'definition_count': definition_count,
        'confidence_with_definition': confidence_with_definition
    }

def generate_html(data, output_path):
    """
    Generate an HTML page with the row count, pie charts, and bar charts.
    
    Args:
        data (dict): Dictionary containing analysis data
        output_path (str): Path to save the HTML file
    """
    # Define the fixed color mapping for NIST Cybersecurity Framework functions
    cyber_color_mapping = {
        'GOVERN': '#f9d765',  # giallo
        'IDENTIFY': '#5671f9', # blu
        'DETECT': '#ee855b',   # arancione
        'PROTECT': '#9c5bf9',  # viola
        'RESPOND': '#f95b5b',  # rosso
        'RECOVER': '#5bf977'   # verde
    }
    
    # Define the fixed color mapping for NIST Privacy Framework functions
    privacy_color_mapping = {
        'IDENTIFY-P': '#f95b5b',  # rosso
        'GOVERN-P': '#f9d765',    # giallo
        'CONTROL-P': '#9c5bf9',   # viola
        'COMMUNICATE-P': '#40E0D0', # verde acqua
        'PROTECT-P': '#5671f9'    # blu
    }
    
    # Prepare data for the Cybersecurity Framework pie chart
    cyber_functions = ['GOVERN', 'IDENTIFY', 'PROTECT', 'DETECT', 'RESPOND', 'RECOVER']
    cyber_labels = cyber_functions.copy()
    cyber_colors = [cyber_color_mapping[func] for func in cyber_functions]
    
    # Create values array with same order as labels for Cybersecurity Framework
    cyber_values = []
    for function in cyber_functions:
        if function in data['cyber_prefix_counts']:
            cyber_values.append(data['cyber_prefix_counts'][function])
        else:
            cyber_values.append(0)
    
    # Calculate total excerpts for Cybersecurity Framework
    cyber_total = sum(data['cyber_prefix_counts'].values())
    
    # Add any other functions that might be in the data but not in our predefined list
    for function, count in data['cyber_prefix_counts'].items():
        if function not in cyber_functions:
            cyber_labels.append(function)
            cyber_values.append(count)
            # Use a default color for unknown functions
            cyber_colors.append('#999999')
    
    # Prepare data for the Privacy Framework pie chart
    privacy_functions = ['IDENTIFY-P', 'GOVERN-P', 'CONTROL-P', 'COMMUNICATE-P', 'PROTECT-P']
    privacy_labels = privacy_functions.copy()
    privacy_colors = [privacy_color_mapping[func] for func in privacy_functions]
    
    # Create values array with same order as labels for Privacy Framework
    privacy_values = []
    for function in privacy_functions:
        if function in data['privacy_prefix_counts']:
            privacy_values.append(data['privacy_prefix_counts'][function])
        else:
            privacy_values.append(0)
    
    # Calculate total excerpts for Privacy Framework
    privacy_total = sum(data['privacy_prefix_counts'].values())
    
    # Add any other functions that might be in the data but not in our predefined list
    for function, count in data['privacy_prefix_counts'].items():
        if function not in privacy_functions:
            privacy_labels.append(function)
            privacy_values.append(count)
            # Use a default color for unknown functions
            privacy_colors.append('#999999')
    
    # Convert to JavaScript array strings
    cyber_colors_str = "[" + ", ".join([f"'{color}'" for color in cyber_colors]) + "]"
    privacy_colors_str = "[" + ", ".join([f"'{color}'" for color in privacy_colors]) + "]"
    
    # Prepare data for the confidence bar chart
    conf_labels = ['High confidence', 'Medium confidence', 'Low confidence', 'Marked as definition']
    conf_values = [
        data['confidence_counts']['high'],
        data['confidence_counts']['medium'],
        data['confidence_counts']['low'],
        data['definition_count']
    ]
    conf_colors = ['#006D5B', '#00A693', '#40E0D0', '#7FFFD4']  
    conf_colors_str = "['" + "', '".join(conf_colors) + "']"
    
    # Prepare data for the confidence with definitions bar chart
    conf_def_labels = ['High confidence', 'Medium confidence', 'Low confidence']
    conf_def_values = [
        data['confidence_with_definition']['high'],
        data['confidence_with_definition']['medium'],
        data['confidence_with_definition']['low']
    ]
    conf_def_colors = ['#A6FFE6', '#C2FFEE', '#D8FFF5']
    conf_def_colors_str = "['" + "', '".join(conf_def_colors) + "']"
    
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CSV Visualization</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 10px;
        }}
        h1 {{
            color: #333;
            margin-top: 10px;
            margin-bottom: 8px;
            font-size: 18px;
        }}
        .chart-title {{
            color: #333;
            margin: 5px 0;
            font-size: 14px;
            text-align: center;
            font-weight: bold;
        }}
        .total-count {{
            font-size: 14px;
            margin-bottom: 10px;
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
            position: relative;
        }}
        .chart-container {{
            width: 100%;
            height: 210px;
            margin-top: 5px;
        }}
        .pie-container {{
            width: 75%;
            height: 210px;
            margin-top: 5px;
            margin-left: auto;
            margin-right: auto;
            position: relative;
            display: flex;
            justify-content: center;
        }}
        .bar-chart-container {{
            width: 85%; /* Reduced width for bar charts */
            height: 210px;
            margin-top: 5px;
            margin-left: auto;
            margin-right: auto;
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
    </style>
</head>
<body>
    <h1>CSV Visualization</h1>
    
    <div class="total-count">
        <strong>Total number of excerpts: {data['total_rows']}</strong>
    </div>
    
    <div class="grid-container">
        <!-- First row - two pie charts side by side -->
        <div class="chart-wrapper">
            <div class="chart-title">NIST Cybersecurity Framework Functions: {cyber_total} excerpts</div>
            <div class="pie-container">
                <canvas id="cyberPieChart"></canvas>
            </div>
        </div>
        
        <div class="chart-wrapper">
            <div class="chart-title">NIST Privacy Framework Functions: {privacy_total} excerpts</div>
            <div class="pie-container">
                <canvas id="privacyPieChart"></canvas>
            </div>
        </div>
        
        <!-- Second row - two bar charts side by side -->
        <div class="chart-wrapper">
            <div class="chart-title">Distribution by confidence and definitions</div>
            <div class="chart-description">Number of excerpts by confidence level and definitions</div>
            <div class="bar-chart-container">
                <canvas id="confidenceChart"></canvas>
            </div>
        </div>
        
        <div class="chart-wrapper">
            <div class="chart-title">Definitions by confidence level</div>
            <div class="chart-description">Rows with each confidence level marked as definitions</div>
            <div class="bar-chart-container">
                <canvas id="confDefChart"></canvas>
            </div>
        </div>
    </div>

    <script>
        // PIE CHART - Cybersecurity Framework
        const cyberLabels = {str(cyber_labels)};
        const cyberValues = {str(cyber_values)};
        const cyberColors = {cyber_colors_str};
        
        const cyberCtx = document.getElementById('cyberPieChart').getContext('2d');
        new Chart(cyberCtx, {{
            type: 'pie',
            data: {{
                labels: cyberLabels,
                datasets: [{{
                    data: cyberValues,
                    backgroundColor: cyberColors,
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
                                const percentage = value > 0 ? Math.round((value / total) * 100) : 0;
                                return `${{label}}: ${{value}} (${{percentage}}%)`;
                            }}
                        }}
                    }}
                }}
            }}
        }});
        
        // PIE CHART - Privacy Framework
        const privacyLabels = {str(privacy_labels)};
        const privacyValues = {str(privacy_values)};
        const privacyColors = {privacy_colors_str};
        
        const privacyCtx = document.getElementById('privacyPieChart').getContext('2d');
        new Chart(privacyCtx, {{
            type: 'pie',
            data: {{
                labels: privacyLabels,
                datasets: [{{
                    data: privacyValues,
                    backgroundColor: privacyColors,
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
                                const percentage = value > 0 ? Math.round((value / total) * 100) : 0;
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

def main(csv_file_path, output_dir='output'):
    """
    Main function to process the CSV file and generate an HTML visualization.
    
    Args:
        csv_file_path (str): Path to the CSV file
        output_dir (str): Directory to save output files
    """
    # Create output directory if it doesn't exist
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Process the CSV file
    data = process_csv(csv_file_path)
    
    # Get the input filename without path and extension for the output filename
    input_filename = os.path.basename(csv_file_path)
    input_filename_no_ext = os.path.splitext(input_filename)[0]
    output_filename = f"{input_filename_no_ext} results.html"
    
    # Generate HTML with charts
    html_path = os.path.join(output_dir, output_filename)
    generate_html(data, html_path)
    
    # Print summary information
    print(f"Total rows processed: {data['total_rows']}")
    print("\nCybersecurity Framework Function Counts:")
    for function, count in data['cyber_prefix_counts'].items():
        print(f"  {function}: {count}")
    
    print("\nPrivacy Framework Function Counts:")
    for function, count in data['privacy_prefix_counts'].items():
        print(f"  {function}: {count}")
    
    print(f"\nConfidence counts: High={data['confidence_counts']['high']}, Medium={data['confidence_counts']['medium']}, Low={data['confidence_counts']['low']}")
    print(f"Rows marked as definition: {data['definition_count']}")
    print(f"Definitions by confidence: High={data['confidence_with_definition']['high']}, Medium={data['confidence_with_definition']['medium']}, Low={data['confidence_with_definition']['low']}")
    print(f"\nVisualization generated at: {html_path}")
    print(f"Open the HTML file in a web browser to view the visualization")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        csv_file_path = sys.argv[1]
    else:
        csv_file_path = "A proinnovation approach to AI regulation UK AI Act 1 of 3.csv"
    
    main(csv_file_path)
