$(function() {
    //request for Shawn
    $('.panel-support').on('click', function(){
      var panelId = $(this).attr('data-panelid');
      $('#'+panelId).toggle(200);
    });

    $('#shawnPanelsfid').on('keyup', function(){
        $('#previewShawn').show("slow", function(){
        });
        var shawnNumber = $('#shawnPanelsfid').val();
        var shawnName = ' ' + $('#'+shawnNumber).text();
        $('#previewShawn .panel-heading').html('Preview: ' + shawnNumber + shawnName);
        var shawnInstallLink = $('#'+shawnNumber+'install').attr("href");
        $('#previewShawn #shawnPanelBody2').html("Can you please see if this is doable? Link here: " + shawnInstallLink);
    });

    $(".dropdown-shawn li a").click(function(){
      var selText = $(this).text();
      $(this).parents('.form-group').find('.dropdown-toggle').html(selText+' <span class="caret"></span>');
      $('#shawnIssue').val($(this).html());
      var subject = $('#previewShawn .panel-heading').text();
      $('#previewShawn .panel-heading').html(subject +' - ' + selText);
    });

    $('#shawnSend').click(function(){
      $("#shawnResult").text('');
      $('#shawnLoading').show();
      var shawnSubject = $('#previewShawn .panel-heading').text();
      var shawnContent = $('#previewShawn #shawnPanelBody2').text();
      var shawnMsg = $('#previewShawn #shawnPanelBody3').text();
      $.getJSON('/shawnMail', {
        shawnSubject: $('#previewShawn .panel-heading').text(),
        shawnContent: $('#previewShawn #shawnPanelBody2').text(),
        shawnMsg: $('#previewShawn #shawnPanelBody3').text(),
      }, function(data) {
        $('#shawnLoading').hide();
        $("#shawnResult").text(data.result);
      });
    });



    //less than 12 months calc
    $('a#lessthan12').bind('click', function() {
      $.getJSON('/background_process', {
        months: $('input[name="months"]').val(),
        sfid: $('input[name="sfid"]').val(),
        consumption: $('input[name="consumption"]').val(),
      }, function(data) {
        $("#consum").text(data.result);
      });
      return false;
    });

    //Fetch Install Packs
    $('a#futureInstall').bind('click', function() {
      $.getJSON('/fetchInstallPack', {
        sfidInstall: $('input[name="sfidInstall"]').val(),
      }, function(data) {
        $("#installResult").text(data.result);
      });
      return false;
    });

    //case close final check
    // $('#caseClose').bind('click', function(){
    //   alert($('#caseClose').text());
    // })

    //tooltip
    $('[data-toggle="tooltip"]').tooltip();
    
    $('#infoNew').on('show.bs.modal', function (event) {
      var button = $(event.relatedTarget) // Button that triggered the modal
      var recipient = button.data('whatever') // Extract info from data-* attributes
      var sf = button.data('number')
      var amp = button.data('amp') 
      var rsi = button.data('rsi')
      var rsp = button.data('rsp')
      var au = button.data('au')
      var note = button.data('note')
      var cklist = button.data('cklist').split(",")
      var modal = $(this)
      for (var i = cklist.length - 1; i >= 0; i--) {
        if (cklist[i]) {
          $("#new_ckList"+String(i)).prop("checked", true)
        } else {
          $("#new_ckList"+String(i)).prop("checked", false)
        }
      }
      modal.find('.modal-title').text(recipient)
      $('#total-amperage').val(amp)
      $('#rafter-sizing').val(rsi)
      $('#rafter-spacing').val(rsp)
      $('#annual-usage').val(au)
      $('#design-note').val(note)
      $('#form-info').attr("action","/caseinfo/" + sf)
    })
    

    $('#infoSurvey').on('show.bs.modal', function (event) {
      var button = $(event.relatedTarget) // Button that triggered the modal
      var recipient = button.data('whatever') // Extract info from data-* attributes
      var sf = button.data('number')
      var amp = button.data('amp') 
      var rsi = button.data('rsi')
      var rsp = button.data('rsp')
      var au = button.data('au')
      var note = button.data('note')
      var cklist = button.data('cklist').split(",")
      for (var i = cklist.length - 1; i >= 0; i--) {
        if (cklist[i]) {
          $("#survey_ckList"+String(i)).prop("checked", true)
        } else {
          $("#survey_ckList"+String(i)).prop("checked", false)
        }
      }
      var modal = $(this)
      modal.find('.modal-title').text(recipient)
      $('#t-a').val(amp)
      $('#r-si').val(rsi)
      $('#r-sp').val(rsp)
      $('#a-u').val(au)
      $('#d-n').val(note)
      $('#f-i').attr("action","/caseinfo_survey/" + sf)
    })
    
    $('#infoModalClose').on('show.bs.modal', function (event) {
      var button = $(event.relatedTarget) // Button that triggered the modal
      var recipient = button.data('whatever') // Extract info from data-* attributes
      var qc = button.data('qc') 
      var it = button.data('it')
      var cad = button.data('cad')
      var prb = button.data('prb')
      var note = button.data('note')
      var sfcd = button.data('sfcd')

      var modal = $(this)
      modal.find('.modal-title').text('Closing details for: ' + recipient)
      $('#check-by').val(qc)
      $('#box-install').val(it)
      $('#cad-pack').val(cad)
      $('#prb-status').val(prb)
      $('#Note').val(note)
    })
    
    $('#infoModalReject').on('show.bs.modal', function (event) {
      var button = $(event.relatedTarget) // Button that triggered the modal
      var recipient = button.data('whatever') // Extract info from data-* attributes
      var sf = button.data('number')
      var note = button.data('note')
      var modal = $(this)
      modal.find('.modal-title').text('Comments for: ' + recipient)
      $('#reject_note').val(note)
      $('#form-reject').attr("action","/casereject/" + sf)
    })
    
    
    $('#infoModal3').on('show.bs.modal', function (event) {
      var button = $(event.relatedTarget) // Button that triggered the modal
      var recipient = button.data('whatever') // Extract info from data-* attributes
      var info = button.data('info')
      var note = button.data('note')
      var cklist = button.data('cklist').split(",")
      var modal = $(this)
      console.log(recipient)
      modal.find('.modal-title').text('Update SQL for: ' + recipient)
      $('#Info').val(info)
      $('#Note_Joey').val(note)
      for (var i = cklist.length - 1; i >= 0; i--) {
        if (cklist[i]) {
          $("#ckList"+String(i)).prop("checked", true)
        } else {
          $("#ckList"+String(i)).prop("checked", false)
        }
      }
      $('#form-joey').attr("action","/joeyinfo/" + recipient)
    })
    
    $('#infoModal_archive').on('show.bs.modal', function (event) {
      var button = $(event.relatedTarget) // Button that triggered the modal
      var recipient = button.data('whatever') // Extract info from data-* attributes
      var info = button.data('info')
      var note = button.data('note')
      var prb = button.data('prb')
      var cklist = button.data('cklist').split(",")
      console.log(cklist)
      var modal = $(this)
      modal.find('.modal-title').text('Update SQL for: ' + recipient)
      $('#Info').val(info)
      $('#Note').val(note)
      $('#PRB').val(prb)
      for (var i = cklist.length - 1; i >= 0; i--) {
        if (cklist[i]) {
          $("#ckList"+String(i)).attr("checked", cklist[i])
        } else {
          $("#ckList"+String(i)).removeAttr("checked")
        }
      }
      $('#form-joey').attr("action","/joeyinfo/" + recipient)
    })
    
    $(".dropdown-designer li a").click(function(){
      var selText = $(this).text();
      $(this).parents('.btn-group').find('.dropdown-toggle').html(selText+' <span class="caret"></span>');
    });
    
    $(".dropdown-menu li a").click(function(){
      var selText = $(this).text();
      $(this).parents('.btn-group').find('.dropdown-toggle').html(selText+' <span class="caret"></span>');
      $('#status').val($(this).html());
    });
    
    var hash = window.location.hash;
    hash && $('ul.nav a[href="' + hash + '"]').tab('show');
    $('.nav-tabs a').click(function (e) {
      $(this).tab('show');
      var scrollmem = $('body').scrollTop();
      window.location.hash = this.hash;
      $('html,body').scrollTop(scrollmem);
    });

});