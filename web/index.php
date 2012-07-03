<!DOCTYPE html>
<html>
<head>
  <title>OCC Worship Videos</title>
  <style type="text/css">

    body {
      background-color: black;
      color: white;
    }
    
    #player {
      position: fixed;
      left: 5px;
      top: 5px;
      display: block;
      width: 670px;
      height: 380px;
    }

    #video-table-container {
      position: absolute;
      top: 5px;
      left: 690px;
    }

    #video-table th {
      text-align: left;
    }

    #video-table td,
    #video-table th {
      padding: 5px;
    }

  </style>
</head>
<body>
<script type='text/javascript' src='jwplayer/jwplayer.js'></script>

<!--
<div id='mediaplayer'></div>

<script type="text/javascript">
  jwplayer('mediaplayer').setup({
    'flashplayer': 'jwplayer/player.swf',
    'id': 'playerID',
    'width': '480',
    'height': '270',
    'file': 'media/occ-stream-test-trim.flv'
  });
</script>
-->
<script type="text/javascript" src="flowplayer/flowplayer-3.2.10.min.js"></script>
<a style="display:block;width:670px;height:380px;"
   id="player"></a>
</body>
<script type="text/javascript">
  flowplayer("player", "flowplayer/flowplayer-3.2.11.swf", {
    playlist: []
  });

  function playVideo(suffix)
  {
      $f("player").play("./media/" + suffix);
  }
</script>
<div id="video-table-container">
<table id="video-table">
  <tr>
    <th>File</th>
    <th>Actions</th>
    <th>Date Modified</th>
  </tr>
<?
  $dir = "./media/";
  $dh = opendir($dir);
  $list = array();

  while ($file = readdir($dh))
  {
    $ft = filetype($dir . $file);
    if ($ft == "file")
    {
      $fmtime = filemtime($dir . $file);
      $list[$file] = $file;
    }
  }

  krsort($list);

  foreach ($list as $file)
  {
    $fmtime = filemtime($dir . $file);
    $fmdate = date("F d Y H:i:s", $fmtime);
    print "<tr>\n";
    print "<td><a href=\"javascript:playVideo('$file')\">$file</a></td>\n";
    print "<td>";
    print "<a href=\"javascript:playVideo('$file')\">Play</a> | ";
    print "<a href=\"./media/$file\">Download</a>";
    print "</td>\n";
    print "<td>$fmdate</td>\n";
    print "</tr>\n";
  }
?>
</table>
</table>
</html>
