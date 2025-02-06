import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-page1',
  templateUrl: './page1.component.html',
  styleUrls: ['./page1.component.css']
})
export class Page1Component implements OnInit {
  corporateActions: string[] = [];  // Store corporate actions dynamically
  selectedAction: string | null = null;
  tableData: any[] = [];
  filteredData: any[] = [];  // Store filtered table data
  apiUrl: string = 'http://74.249.184.110:8000/get-records-today/';

  selectedExtractedInfo: string | null = null;
  parsedExtractedInfo: { key: string, value: string }[] = [];
  currentSelectedRow: any | null = null;  // Store the currently selected row

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.fetchCorporateActions();
  }

  fetchCorporateActions(): void {
    this.http.get<any[]>(this.apiUrl).subscribe({
      next: (data) => {
        // Extract unique corporate actions from the fetched data
        this.corporateActions = [...new Set(data.map(record => record.corporate_action))];
        
        // Map the data to include formatted date and other necessary fields
        this.tableData = data.map(record => ({
          dateTime: this.formatDate(record.insertion_date_time), // Format date
          company: record.company,
          action: record.corporate_action,
          announcementDate: this.formatDate(record.date_announcement), // Format date
          source: record.source,
          extractedInfo: record.extracted_information,
          verification: record.status || 'Pending'
        }));

        // Initially, show all records
        this.filteredData = this.tableData;
        console.log('Filtered Data:', this.filteredData);
      },
      error: (error) => {
        console.error('Error fetching corporate actions:', error);
      }
    });
  }

  formatDate(dateString: string): string {
    // Format the date to show only the date part, not the time
    const date = new Date(dateString);
    return date.toISOString().split('T')[0]; // Returns date in YYYY-MM-DD format
  }

  showExtractedInfo(extractedInfo: string, row: any): void {
    this.selectedExtractedInfo = extractedInfo;
    this.currentSelectedRow = row;  // Store the row so we can access its source later

    // Parse the extracted information into key-value pairs
    this.parsedExtractedInfo = extractedInfo
      .split('\n')
      .map(line => {
        const parts = line.split(':');
        return { key: parts[0]?.trim(), value: parts[1]?.trim() || 'N/A' };
      })
      .filter(item => item.key && item.value !== 'N/A'); // Remove empty entries and N/A values
  }
  openSourceLink(source: string): void {
    if (source && this.isValidUrl(source)) {
      window.open(source, '_blank');  // Open in new tab
    } else {
      console.error('Invalid source URL');
    }
  }
  
  // Function to check if the URL is valid
  isValidUrl(url: string): boolean {
    const pattern = new RegExp('^(https?:\\/\\/(?:www\\.)?[^\\s]+)$');
    return pattern.test(url);
  }
  
  submitEditedInfo() {
    if (!this.selectedExtractedInfo) return;

    // Convert updated extracted info back to string format
    const updatedExtractedInfo = this.parsedExtractedInfo
      .map(item => `${item.key}: ${item.value}`)
      .join('\n');

    // Find the corresponding row in tableData
    const record = this.tableData.find(row => row.extractedInfo === this.selectedExtractedInfo);

    if (record) {
      record.extractedInfo = updatedExtractedInfo;  // Update extracted info
      record.verification = 'Verified'; // Mark as verified
    }

    // Clear selected extracted info to close the extracted info table
    this.currentSelectedRow = null;  // Clear the selected row
    this.selectedExtractedInfo = null;
  }

  selectAction(action: string): void {
    console.log('Selected Action:', action);  // Debugging line
  
    // Toggle action selection
    if (this.selectedAction === action) {
      this.selectedAction = null;
      this.filteredData = [...this.tableData];  // Show all records
      console.log('Showing all records');
    } else {
      this.selectedAction = action;
      this.filteredData = this.tableData.filter(row => row.action === action);  // Filter records based on selected action
      console.log('Filtered Data:', this.filteredData);  // Debugging line
    }
  }
  

  isSelected(action: string): boolean {
    return this.selectedAction === action;
  }
}
