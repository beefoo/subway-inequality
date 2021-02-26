'use strict';

var App = (function() {

  function App(config) {
    var defaults = {
      t: 0
    };
    var params = queryParams();
    this.opt = $.extend({}, defaults, config, params);
    this.init();
  }

  function queryParams(){
    if (location.search.length) {
      var search = location.search.substring(1);
      return JSON.parse('{"' + search.replace(/&/g, '","').replace(/=/g,'":"') + '"}', function(key, value) { return key===""?value:decodeURIComponent(value) });
    }
    return {};
  };

  App.prototype.init = function(){
    var _this = this;
    var t = parseInt(this.opt.t);

    this.stations = $('.station-time-link').map(function(){
      var $el = $(this);
      return {
        '$el': $el,
        'seconds': parseInt($el.attr('data-seconds'))
      };
    });

    this.selectedIndex = -1;

    this.player = new Plyr('#player');
    this.player.on('canplay', function(e){
      // if (t > 0) {
      //   _this.seekTo(t);
      //   _this.highlightClosestStation(t);
      // }
      _this.loadListeners();
    });

    this.player.on('timeupdate', function(e){
      _this.highlightClosestStation(_this.player.currentTime);
    });

  };

  App.prototype.changeTime = function($link){
    var seconds = parseInt($link.attr('data-seconds'));

    $('.station-time-link').removeClass('selected');
    $link.addClass('selected');

    this.seekTo(seconds);

    $([document.documentElement, document.body]).animate({
        scrollTop: $("#player").offset().top
    }, 1000);

    // // update URL
    // if (window.history.pushState) {
    //   var data = {t: seconds};
    //   var urlEncoded = $.param(data);
    //   var baseUrl = window.location.href.split('?')[0];
    //   var currentState = window.history.state;
    //   var newUrl = baseUrl + '?' + urlEncoded;
    //
    //   // ignore if state is the same
    //   if (currentState) {
    //     var currentUrl = baseUrl + '?' + $.param(currentState);
    //     if (newUrl === currentUrl) return;
    //   }
    //
    //   window.historyInitiated = true;
    //   window.history.replaceState(data, '', newUrl);
    // }
  };

  App.prototype.highlightClosestStation = function(seconds){
    var closestIndex = this.stations.length-1;

    for (var i=0; i<this.stations.length; i++) {
      var station = this.stations[i];
      if (seconds < station.seconds) {
        closestIndex = i-1;
        break;
      }
    }

    closestIndex = Math.min(closestIndex, this.stations.length-1);
    closestIndex = Math.max(closestIndex, 0);

    if (closestIndex !== this.selectedIndex) {
      this.selectedIndex = closestIndex;
      $('.station-time-link').removeClass('selected');
      this.stations[closestIndex].$el.addClass('selected');
    }
  };

  App.prototype.loadListeners = function(){
    var _this = this;

    $('.station-time-link').on('click', function(e){
      e.preventDefault();
      _this.changeTime($(this));
    });
  };

  App.prototype.seekTo = function(seconds){
    this.player.currentTime = seconds;
  };

  return App;

})();

$(function() {
  var app = new App({});
});
