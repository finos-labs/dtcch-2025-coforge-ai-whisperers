import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-page1',
  templateUrl: './page1.component.html',
  styleUrls: ['./page1.component.css']
})
export class Page1Component implements OnInit {
  corporateActions: string[] = [];  
  selectedAction: string | null = null;
  tableData: any[] = [];
  filteredData: any[] = [];  
  apiUrl: string = 'http://74.249.184.110:8000/get-records-today/';
  updateUrl: string = 'http://74.249.184.110:8000/update-corporate-action/';

  selectedExtractedInfo: string | null = null;
  parsedExtractedInfo: { key: string, value: string }[] = [];
  currentSelectedRow: any | null = null;
  isPopupOpen: boolean = false;

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.fetchCorporateActions();
  }

  fetchCorporateActions(): void {
    this.http.get<any[]>(this.apiUrl).subscribe({
      next: (data) => {
        this.corporateActions = [...new Set(data.map(record => record.corporate_action))];
        
        this.tableData = data.map(record => ({
          id: record.id,  // Ensure ID is included
          dateTime: this.formatDate(record.insertion_date_time), 
          company: record.company,
          action: record.corporate_action,
          announcementDate: this.formatDate(record.date_announcement), 
          source: record.source,
          extractedInfo: record.extracted_information,
          verification: record.status || 'Pending'
        }));

        this.filteredData = this.tableData;
        console.log('Table Data:', this.tableData);  // Debugging
      },
      error: (error) => {
        console.error('Error fetching corporate actions:', error);
      }
    });
  }

  formatDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toISOString().split('T')[0];
  }

  openPopup(extractedInfo: string, row: any): void {
    this.isPopupOpen = true;
    this.selectedExtractedInfo = extractedInfo;
    this.currentSelectedRow = row;

    console.log('Selected Row:', this.currentSelectedRow);  // Debugging

    this.parsedExtractedInfo = extractedInfo
      .split('\n')
      .map(line => {
        const parts = line.split(':');
        return { key: parts[0]?.trim(), value: parts[1]?.trim() || 'N/A' };
      })
      .filter(item => item.key && item.value !== 'N/A');
  }

  closePopup(): void {
    this.isPopupOpen = false;
  }

  showExtractedInfo(extractedInfo: string, row: any): void {
    this.selectedExtractedInfo = extractedInfo;
    this.currentSelectedRow = row;

    console.log('Selected Row for Edit:', this.currentSelectedRow);  // Debugging

    this.parsedExtractedInfo = extractedInfo
      .split('\n')
      .map(line => {
        const parts = line.split(':');
        return { key: parts[0]?.trim(), value: parts[1]?.trim() || 'N/A' };
      })
      .filter(item => item.key && item.value !== 'N/A');
  }

  openSourceLink(source: string): void {
    if (source && this.isValidUrl(source)) {
      // Open external URLs directly
      window.open(source, '_blank');
    } else if (source && source.endsWith('.pdf')) {
      // Open PDFs directly from assets
      const pdfUrl = `assets/Master_CA_PDFS/${source}`;
      window.open(pdfUrl, '_blank');
    } else if (source && source.endsWith('.csv')) {
      // Fetch CSV file and display in a new tab
      this.displayCSVInNewTab(`assets/${source}`);
    } else {
      console.error('Invalid source URL or unsupported file type');
    }
  }
  
  displayCSVInNewTab(csvUrl: string): void {
    this.http.get(csvUrl, { responseType: 'text' }).subscribe({
      next: (csvContent) => {
        const parsedTable = this.convertCSVToHTML(csvContent);
        const newWindow = window.open('', '_blank');
        if (newWindow) {
          newWindow.document.write(`
            <html>
              <head>
                <title>CSV Viewer</title>
                <style>
                  table { border-collapse: collapse; width: 100%; }
                  th, td { border: 1px solid black; padding: 8px; text-align: left; }
                  th { background-color: #f2f2f2; }
                </style>
              </head>
              <body>
                <h2>CSV File Contents</h2>
                ${parsedTable}
              </body>
            </html>
          `);
          newWindow.document.close();
        }
      },
      error: (err) => {
        console.error('Error fetching CSV file:', err);
      }
    });
  }
  
  convertCSVToHTML(csv: string): string {
    const rows = csv.split('\n').map(row => row.split(','));
    if (rows.length === 0) return '<p>No data found in CSV</p>';
  
    let tableHTML = '<table><thead><tr>';
    tableHTML += rows[0].map(col => `<th>${col.trim()}</th>`).join('');
    tableHTML += '</tr></thead><tbody>';
  
    for (let i = 1; i < rows.length; i++) {
      tableHTML += '<tr>' + rows[i].map(col => `<td>${col.trim()}</td>`).join('') + '</tr>';
    }
  
    tableHTML += '</tbody></table>';
    return tableHTML;
  }
  
  isValidUrl(url: string): boolean {
    const pattern = new RegExp('^(https?:\\/\\/(?:www\\.)?[^\\s]+)$');
    return pattern.test(url);
  }
  
  submitEditedInfo() {
    if (!this.selectedExtractedInfo || !this.currentSelectedRow?.id) {
      console.error("Error: Missing required data (Extracted Info or Row ID)");
      return;
    }
  
    const updatedExtractedInfo = this.parsedExtractedInfo
      .map(item => `${item.key}: ${item.value}`)
      .join('\n');
  
    const record = this.tableData.find(row => row.extractedInfo === this.selectedExtractedInfo);
  
    if (record) {
      record.extractedInfo = updatedExtractedInfo;  
      record.verification = 'Verified';
    }

    const payload = {
      id: this.currentSelectedRow.id,  
      Extracted_Information: updatedExtractedInfo
    };

    console.log('Submitting Payload:', payload);  // Debugging

    this.http.put(this.updateUrl, payload, {
      headers: { 'Content-Type': 'application/json' }
    }).subscribe({
      next: (response) => {
        console.log('Update successful:', response);
      },
      error: (error) => {
        console.error('Error updating extracted information:', error);
      }
    });

    this.currentSelectedRow = null;  
    this.selectedExtractedInfo = null;
    this.isPopupOpen = false;
  }
  

  selectAction(action: string): void {
    console.log('Selected Action:', action);
  
    if (this.selectedAction === action) {
      this.selectedAction = null;
      this.filteredData = [...this.tableData];
      console.log('Showing all records');
    } else {
      this.selectedAction = action;
      this.filteredData = this.tableData.filter(row => row.action === action);
      console.log('Filtered Data:', this.filteredData);
    }
  }

  isSelected(action: string): boolean {
    return this.selectedAction === action;
  }
}
