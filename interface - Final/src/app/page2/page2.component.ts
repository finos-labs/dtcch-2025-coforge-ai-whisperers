import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-page1',
  templateUrl: './page2.component.html',
  styleUrls: ['./page2.component.css']
})
export class Page2Component implements OnInit {
  corporateActions: string[] = [];  
  selectedAction: string | null = null;
  tableData: any[] = [];
  filteredData: any[] = [];  
  apiUrl: string = 'http://74.249.184.110:8000/get-records-before-today/';
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
      window.open(source, '_blank');
    } else {
      console.error('Invalid source URL');
    }
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
