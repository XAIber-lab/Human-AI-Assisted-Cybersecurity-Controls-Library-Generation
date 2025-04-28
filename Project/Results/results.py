import csv
import os
import re

def process_csv(csv_file_path):
    """
    Process a CSV file to analyze first proposals, confidence values, and definitions.
    
    Args:
        csv_file_path (str): Path to the CSV file
        
    Returns:
        dict: A dictionary containing total row count, prefix counts,
              confidence counts, definition count, and confidence with definition counts
    """
    # Initialize data structures
    total_rows = 0
    prefix_counts = {}
    confidence_counts = {'high': 0, 'medium': 0, 'low': 0}
    definition_count = 0
    confidence_with_definition = {'high': 0, 'medium': 0, 'low': 0}
    
    # Read the CSV file
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        # Read the first line to get headers
        header_line = file.readline().strip()
        headers = header_line.split('_')
        
        # Find the indexes of required columns
        try:
            first_proposal_index = headers.index('first proposal')
            confidence_index = headers.index('confidence')
            definitions_index = headers.index('definitions')
        except ValueError as e:
            raise ValueError(f"Required column not found in the CSV file: {e}")
        
        # Process each line
        for line in file:
            if line.strip():  # Skip empty lines
                total_rows += 1
                fields = line.strip().split('_')
                
                # Ensure there are enough fields
                if len(fields) > max(first_proposal_index, confidence_index, definitions_index):
                    # Process first proposal
                    first_proposal = fields[first_proposal_index]
                    first_part = first_proposal.split(';')[0].strip()
                    if len(first_part) >= 2:
                        prefix = first_part[:2]
                        prefix_counts[prefix] = prefix_counts.get(prefix, 0) + 1
                    
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
    
    # Map prefixes to full names based on the image provided
    prefix_mapping = {
        'GV': 'GOVERN',
        'ID': 'IDENTIFY',
        'PR': 'PROTECT',
        'DE': 'DETECT',
        'RS': 'RESPOND',
        'RC': 'RECOVER'
    }
    
    # Replace prefix keys with full names
    named_counts = {}
    for prefix, count in prefix_counts.items():
        full_name = prefix_mapping.get(prefix, prefix)
        named_counts[full_name] = count
    
    return {
        'total_rows': total_rows,
        'prefix_counts': named_counts,
        'confidence_counts': confidence_counts,
        'definition_count': definition_count,
        'confidence_with_definition': confidence_with_definition
    }

def generate_html(data, output_path):
    """
    Generate an HTML page with the row count, pie chart, and bar charts.
    
    Args:
        data (dict): Dictionary containing analysis data
        output_path (str): Path to save the HTML file
    """
    # Prepare data for the Chart.js pie chart
    pie_labels = list(data['prefix_counts'].keys())
    pie_values = list(data['prefix_counts'].values())
    
    # Create color mapping for pie chart
    pie_colors = ['#f9d765', '#5671f9', '#9c5bf9', '#ee855b', '#f95b5b', '#5bf977']
    pie_colors_str = "[" + ", ".join([f"'{color}'" for color in pie_colors[:len(pie_labels)]]) + "]"
    
    # Prepare data for the confidence bar chart
    conf_labels = ['High confidence', 'Medium confidence', 'Low confidence', 'Marked as definition']
    conf_values = [
        data['confidence_counts']['high'],
        data['confidence_counts']['medium'],
        data['confidence_counts']['low'],
        data['definition_count']
    ]
    conf_colors = ['#00cc44', '#ffcc00', '#ff3333', '#3366ff']  # Green, Yellow, Red, Blue
    conf_colors_str = "['" + "', '".join(conf_colors) + "']"
    
    # Prepare data for the confidence with definitions bar chart
    conf_def_labels = ['High confidence', 'Medium confidence', 'Low confidence']
    conf_def_values = [
        data['confidence_with_definition']['high'],
        data['confidence_with_definition']['medium'],
        data['confidence_with_definition']['low']
    ]
    conf_def_colors = conf_colors[:3]  # Use the same colors as the confidence chart
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
    </style>
</head>
<body>
    <h1>CSV Visualization</h1>
    
    <div class="total-count">
        <strong>Total number of excerpts: {data['total_rows']}</strong>
    </div>
    
    <div class="grid-container">
        <!-- First row - pie chart takes full width -->
        <div class="chart-wrapper full-width">
            <div class="chart-title">Distribution by proposed function (more likely proposal)</div>
            <div class="chart-container">
                <canvas id="pieChart"></canvas>
            </div>
        </div>
        
        <!-- Second row - two bar charts side by side -->
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
        // PIE CHART - Distribution by proposed function
        const pieLabels = {str(pie_labels)};
        const pieValues = {str(pie_values)};
        const pieColors = {pie_colors_str};
        
        const pieCtx = document.getElementById('pieChart').getContext('2d');
        new Chart(pieCtx, {{
            type: 'pie',
            data: {{
                labels: pieLabels,
                datasets: [{{
                    data: pieValues,
                    backgroundColor: pieColors,
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
                                const percentage = Math.round((value / total) * 100);
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
    
    # Generate HTML with charts
    html_path = os.path.join(output_dir, 'visualization.html')
    generate_html(data, html_path)
    
    print(f"Total rows processed: {data['total_rows']}")
    print(f"Confidence counts: High={data['confidence_counts']['high']}, Medium={data['confidence_counts']['medium']}, Low={data['confidence_counts']['low']}")
    print(f"Rows marked as definition: {data['definition_count']}")
    print(f"Definitions by confidence: High={data['confidence_with_definition']['high']}, Medium={data['confidence_with_definition']['medium']}, Low={data['confidence_with_definition']['low']}")
    print(f"Visualization generated at: {html_path}")
    print(f"Open the HTML file in a web browser to view the visualization")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        csv_file_path = sys.argv[1]
    else:
        csv_file_path = "A proinnovation approach to AI regulation UK AI Act 1 of 3.csv"
    
    main(csv_file_path)
