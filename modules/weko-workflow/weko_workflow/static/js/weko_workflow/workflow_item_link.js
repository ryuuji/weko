require([
  "node_modules/jquery/jquery",
  "node_modules/bootstrap/dist/js/bootstrap"
], function () {
  /**
   * Start Loading
   * @param actionButton
   */
  function startLoading(actionButton) {
    actionButton.prop('disabled', true);
    $(".lds-ring-background").removeClass("hidden");
  }

  /**
   * End Loading
   * @param actionButton
   */
  function endLoading(actionButton) {
    actionButton.removeAttr("disabled");
    $(".lds-ring-background").addClass("hidden");
  }

  $('.btn-begin').on('click', function () {
      let _this = $(this);
      startLoading(_this);
      let post_uri = $('#post_uri').text();
      let workflow_id = $(this).data('workflow-id');
      let community = $(this).data('community');
      let post_data = {
          workflow_id: workflow_id,
          flow_id: $('#flow_' + workflow_id).data('flow-id'),
          itemtype_id: $('#item_type_' + workflow_id).data('itemtype-id')
      };
      if(community != ""){
        post_uri = post_uri+"?community="+ community;
      }
      $.ajax({
          url: post_uri,
          method: 'POST',
          async: true,
          contentType: 'application/json',
          data: JSON.stringify(post_data),
          success: function (data, status) {
              if (0 == data.code) {
                  document.location.href = data.data.redirect;
              } else {
                  endLoading(_this);
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {
            endLoading(_this);
          }
      });
  });

  $('#btn-finish').on('click', function(){
    let _this = $(this);
    startLoading(_this);
    let post_uri = $('.cur_step').data('next-uri');
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 0
    };
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function(data, status) {
        if(0 == data.code) {
          if(data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            document.location.href=data.data.redirect;
          } else {
            document.location.reload(true);
          }
        } else {
          endLoading(_this);
          alert(data.msg);
        }
      },
      error: function(jqXHE, status) {
        endLoading(_this);
        alert('server error');
        $('#myModal').modal('hide');
      }
    });
  });

  $('#btn-draft').on('click', function(){
    let _this = $(this);
    startLoading(_this);
    let post_uri = $('.cur_step').data('next-uri');
    let post_data = {
      commond: $('#input-comment').val(),
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 1
    };
    $.ajax({
      url: post_uri,
      method: 'POST',
      async: true,
      contentType: 'application/json',
      data: JSON.stringify(post_data),
      success: function(data, status) {
        if(0 == data.code) {
          if(data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
            document.location.href=data.data.redirect;
          } else {
            document.location.reload(true);
          }
        } else {
          endLoading(_this);
          alert(data.msg);
        }
      },
      error: function(jqXHE, status) {
        endLoading(_this);
        alert('server error');
        $('#myModal').modal('hide');
      }
    });
  });

  $('#btn-approval-req').on('click', function () {
      action_id = $('#hide-actionId').text();
      btn_id = "action_" + action_id;
      $('#' + btn_id).click();
  });

  $('#btn-approval').on('click', function () {
      let _this = $(this);
      startLoading(_this);
      let uri_apo = $('.cur_step').data('next-uri');
      let act_ver = $('.cur_step').data('action-version');
      let post_data = {
          commond: $('#input-comment').val(),
          action_version: act_ver
      };
      $.ajax({
          url: uri_apo,
          method: 'POST',
          async: true,
          contentType: 'application/json',
          data: JSON.stringify(post_data),
          success: function (data, status) {
              if (0 == data.code) {
                  if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
                      document.location.href = data.data.redirect;
                  } else {
                      document.location.reload(true);
                  }
              } else {
                  endLoading(_this);
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {
              endLoading(_this);
              alert('server error');
          }
      });
  });

  $('#btn-reject').on('click', function () {
      let _this = $(this);
      startLoading(_this);
      let uri_apo = $('.cur_step').data('next-uri');
      let act_ver = $('.cur_step').data('action-version');
      let post_data = {
          commond: $('#input-comment').val(),
          action_version: act_ver
      };
      uri_apo = uri_apo+"/rejectOrReturn/0";
      $.ajax({
          url: uri_apo,
          method: 'POST',
          async: true,
          contentType: 'application/json',
          data: JSON.stringify(post_data),
          success: function (data, status) {
              if (0 == data.code) {
                  if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
                      document.location.href = data.data.redirect;
                  } else {
                      document.location.reload(true);
                  }
              } else {
                  endLoading(_this);
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {
              endLoading(_this);
              alert('server error');
          }
      });
  });

  $('#btn-return').on('click', function () {
      let _this = $(this);
      startLoading(_this);
      let uri_apo = $('.cur_step').data('next-uri');
      let act_ver = $('.cur_step').data('action-version');
      let post_data = {
          commond: $('#input-comment').val(),
          action_version: act_ver
      };
      uri_apo = uri_apo+"/rejectOrReturn/1";
      $.ajax({
          url: uri_apo,
          method: 'POST',
          async: true,
          contentType: 'application/json',
          data: JSON.stringify(post_data),
          success: function (data, status) {
              if (0 == data.code) {
                  if (data.hasOwnProperty('data') && data.data.hasOwnProperty('redirect')) {
                      document.location.href = data.data.redirect;
                  } else {
                      document.location.reload(true);
                  }
              } else {
                  endLoading(_this);
                  alert(data.msg);
              }
          },
          error: function (jqXHE, status) {
              endLoading(_this)
              alert('server error');
          }
      });
  });

  $('#lnk_item_detail').on('click', function () {
    $('#myModal').modal('show');
  })
})

//Item Link
function searchResItemLinkCtrl($scope, $rootScope, $http, $location) {
  /**
   * Start Loading
   * @param actionButton
   */
  $scope.startLoading = function (actionButton) {
    actionButton.prop('disabled', true);
    $(".lds-ring-background").removeClass("hidden");
  }

  /**
   * End Loading
   * @param actionButton
   */
  $scope.endLoading = function (actionButton) {
    actionButton.removeAttr("disabled");
    $(".lds-ring-background").addClass("hidden");
  }
  $scope.link_item_list = [];
  $scope.sele_options = [
    { id: "relateTo", content: "relateTo" },
    { id: "isVersionOf", content: "isVersionOf" },
    { id: "hasVersion", content: "hasVersion" },
    { id: "isReplacedBy", content: "isReplacedBy" },
    { id: "replaces", content: "replaces" },
    { id: "isRequiredBy", content: "isRequiredBy" },
    { id: "requires", content: "requires" },
    { id: "isPartOf", content: "isPartOf" },
    { id: "hasPart", content: "hasPart" },
    { id: "isReferencedBy", content: "isReferencedBy" },
    { id: "references", content: "references" },
    { id: "isFormatOf", content: "isFormatOf" },
    { id: "hasFormat", content: "hasFormat" },
    { id: "isSupplementTo", content: "isSupplementTo" },
    { id: "isSupplementedBy", content: "isSupplementedBy" },
    { id: "isIdenticalTo", content: "isIdenticalTo" },
    { id: "isDerivedFrom", content: "isDerivedFrom" },
    { id: "isSourceOf", content: "isSourceOf" }
  ];
  $scope.comment_data = "";

//   add button
  $rootScope.add_link = function(data, index) {
    let sub_data = {
      item_id: 0,
      item_title: "",
      sele_id: ""
    };

    sub_data.sele_id = "relateTo";
    sub_data.item_id = data.metadata.control_number;
    sub_data.item_title = data.metadata.title[0];
    $scope.link_item_list.push(sub_data);
  };

//   add ex_item_link
  $scope.add_ex_link = function (data) {
    let item_data = {
      item_id: "",
      item_title: "",
      sele_id: ""
    };

    item_data.sele_id = data.value;
    item_data.item_id = data.item_links;
    item_data.item_title = data.item_title;
    $scope.link_item_list.push(item_data);
  };

//   delete button
  $scope.del_link = function(index){
    $scope.link_item_list.splice(index, 1);
  };

//   save button
  $scope.btn_save = function () {
    let saveButton = $("#item-link-save-btn");
    $scope.startLoading(saveButton);
    var post_url = $('.cur_step').data('next-uri');
    var post_data = {
      commond: $scope.comment_data,
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 1
    };
    $http({
      method: 'POST',
      url: post_url,
      data: post_data,
      headers: { 'Content-Type': 'application/json' },
    }).then(function successCallback(response) {
      if (0 == response.data.code) {
        if (response.data.hasOwnProperty('data') && response.data.data.hasOwnProperty('redirect')) {
          document.location.href = response.data.data.redirect;
        } else {
          document.location.reload(true);
        }
      } else {
        $scope.endLoading(saveButton);
        alert(response.data.msg);
      }
    }, function errorCallback(response) {
      $scope.endLoading(saveButton);
      alert(response.data.msg);
      document.location.reload(true);
    });
  };
//   run button
  $scope.btn_run=function(){
    let runButton = $("#item-link-run-btn");
    $scope.startLoading(runButton);
    var post_url = $('.cur_step').data('next-uri');
    var post_data = {
      commond: $scope.comment_data,
      action_version: $('.cur_step').data('action-version'),
      temporary_save: 0,
      link_data: $scope.link_item_list
    };
    $scope.isDisabledRun = true;
    $http({
        method: 'POST',
        url: post_url,
        data: post_data,
        headers: {'Content-Type': 'application/json'},
    }).then(function successCallback(response) {
      if(0 == response.data.code) {
        if(response.data.hasOwnProperty('data') && response.data.data.hasOwnProperty('redirect')) {
          document.location.href=response.data.data.redirect;
        } else {
          document.location.reload(true);
        }
      } else {
        $scope.endLoading(runButton);
        alert(response.data.msg);
      }
    }, function errorCallback(response) {
      $scope.endLoading(runButton);
        alert(response.data.msg);
        document.location.reload(true);
    });
  };

// init ex-item links
  $(document).ready(function () {
    let ex_item_links = $("#ex_item_links").val();

    if (ex_item_links !== "" && typeof ex_item_links !== "undefined") {
      json = JSON.parse(ex_item_links);

      json.forEach(function (key) {
        $scope.add_ex_link(key);
      });
    }
  });
}

angular.module('invenioSearch')
  .controller('searchResItemLinkCtrl', searchResItemLinkCtrl);

angular.module('invenioSearch').config(['$interpolateProvider', function($interpolateProvider) {
  $interpolateProvider.startSymbol('{[');
  $interpolateProvider.endSymbol(']}');
}]);
