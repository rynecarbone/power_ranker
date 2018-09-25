$(document).ready(function () {
    $('#power_table').DataTable(
			    { "paging": false,
				    "info"  : false,						
						"searching": false,
					  columnDefs : [
					     { targets:[11],orderData:[11,0]}
				     ],
						 "fnRowCallback": function(nRow, aData, iDisplayIndex, iDisplayIndexFull){
								     if( aData[11] == "1"){$('td', nRow).addClass('row-tier1'); } 
								else if( aData[11] == "2"){$('td', nRow).addClass('row-tier2'); } 
								else if( aData[11] == "3"){$('td', nRow).addClass('row-tier3'); } 
								else if( aData[11] == "4"){$('td', nRow).addClass('row-tier4'); } 
								else if( aData[11] == "5"){$('td', nRow).addClass('row-tier5'); } 
						}
		    	}
		);
});

