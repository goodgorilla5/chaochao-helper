javascript:(function(){
    /* 1. 填寫供應單位代號 */
    var txtBox = document.getElementById('ctl00_contentPlaceHolder_txtSupplyNo');
    var hfld = document.getElementById('ctl00_contentPlaceHolder_hfldSupplyNo');
    if(txtBox) txtBox.value = 'S00076 燕巢區農會';
    if(hfld) hfld.value = 'S00076';

    /* 2. 觸發農委會網頁的 PostBack 下載動作 (4碼) */
    var btn = document.getElementById('ctl00_contentPlaceHolder_btnQuery2');
    if(btn) {
        btn.click();
    } else {
        alert('找不到下載按鈕，請確認是否已切換為電腦版網站');
    }
})();