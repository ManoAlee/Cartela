using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Web.Script.Serialization;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Controls.Primitives;
using System.Windows.Data;
using System.Windows.Input;
using System.Windows.Media;
using System.Windows.Media.Effects;
using System.Windows.Media.Imaging;
using System.Windows.Shapes;
using System.Windows.Shell;
using Microsoft.Win32;

namespace CartelaUI
{
    internal static class Theme
    {
        public static readonly SolidColorBrush BgCanvas = Brush("#F8FAFC");
        public static readonly SolidColorBrush BgSurface = Brush("#FFFFFF");
        public static readonly SolidColorBrush BgMuted = Brush("#F1F5F9");
        public static readonly SolidColorBrush BgHover = Brush("#E2E8F0");
        public static readonly SolidColorBrush Border = Brush("#E2E8F0");
        public static readonly SolidColorBrush BorderStrong = Brush("#CBD5E1");
        public static readonly SolidColorBrush TextPrimary = Brush("#0F172A");
        public static readonly SolidColorBrush TextSecondary = Brush("#475569");
        public static readonly SolidColorBrush TextMuted = Brush("#64748B");

        public static readonly SolidColorBrush Emerald = Brush("#16A34A");
        public static readonly SolidColorBrush EmeraldLight = Brush("#DCFCE7");
        public static readonly SolidColorBrush EmeraldDark = Brush("#15803D");

        public static readonly SolidColorBrush Gold = Brush("#D97706");
        public static readonly SolidColorBrush GoldLight = Brush("#FEF3C7");
        public static readonly SolidColorBrush GoldBorder = Brush("#F59E0B");
        public static readonly SolidColorBrush GoldText = Brush("#B45309");

        public static readonly SolidColorBrush Blue = Brush("#0284C7");
        public static readonly SolidColorBrush BlueLight = Brush("#E0F2FE");
        public static readonly SolidColorBrush Danger = Brush("#DC2626");
        public static readonly SolidColorBrush DangerLight = Brush("#FEE2E2");

        public static SolidColorBrush Brush(string hex)
        {
            var c = (Color)ColorConverter.ConvertFromString(hex);
            var b = new SolidColorBrush(c);
            b.Freeze();
            return b;
        }

        public static DropShadowEffect CardShadow()
        {
            var eff = new DropShadowEffect
            {
                Color = Color.FromRgb(15, 23, 42),
                Direction = 270,
                ShadowDepth = 2,
                BlurRadius = 14,
                Opacity = 0.06
            };
            eff.Freeze();
            return eff;
        }
    }

    public sealed class EngineBridge
    {
        private readonly string _pythonExe;
        private readonly string _cliPath;
        private readonly JavaScriptSerializer _json = new JavaScriptSerializer { MaxJsonLength = int.MaxValue };

        public EngineBridge()
        {
            string baseDir = AppDomain.CurrentDomain.BaseDirectory;
            _cliPath = LocateCli(baseDir);
            _pythonExe = LocatePython();
        }

        private static string LocateCli(string startDir)
        {
            var dir = new DirectoryInfo(startDir);
            for (int i = 0; i < 6 && dir != null; i++)
            {
                string candidate = System.IO.Path.Combine(dir.FullName, "app_files", "src", "core", "engine_cli.py");
                if (File.Exists(candidate)) return candidate;
                candidate = System.IO.Path.Combine(dir.FullName, "src", "core", "engine_cli.py");
                if (File.Exists(candidate)) return candidate;
                candidate = System.IO.Path.Combine(dir.FullName, "engine_cli.py");
                if (File.Exists(candidate)) return candidate;
                dir = dir.Parent;
            }
            return "app_files\\src\\core\\engine_cli.py";
        }

        private static string LocatePython()
        {
            string[] candidates = new[]
            {
                System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python313", "python.exe"),
                System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python312", "python.exe"),
                System.IO.Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "Programs", "Python", "Python311", "python.exe"),
                "python.exe"
            };
            foreach (string c in candidates)
            {
                if (c == "python.exe" || File.Exists(c)) return c;
            }
            return "python.exe";
        }

        public async Task<Dictionary<string, object>> CallAsync(string command, object payload = null)
        {
            return await Task.Run(() =>
            {
                string jsonArg = payload == null ? "{}" : _json.Serialize(payload);
                var psi = new ProcessStartInfo
                {
                    FileName = _pythonExe,
                    Arguments = string.Format("\"{0}\" {1} -", _cliPath, command),
                    UseShellExecute = false,
                    RedirectStandardInput = true,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true,
                    StandardOutputEncoding = Encoding.UTF8,
                    StandardErrorEncoding = Encoding.UTF8
                };
                psi.EnvironmentVariables["PYTHONIOENCODING"] = "utf-8";
                using (var proc = Process.Start(psi))
                {
                    proc.StandardInput.Write(jsonArg);
                    proc.StandardInput.Close();
                    string stdout = proc.StandardOutput.ReadToEnd();
                    string stderr = proc.StandardError.ReadToEnd();
                    proc.WaitForExit(35000);
                    if (string.IsNullOrWhiteSpace(stdout))
                    {
                        return new Dictionary<string, object>
                        {
                            { "ok", false },
                            { "error", string.IsNullOrWhiteSpace(stderr) ? "Sem resposta do motor." : stderr.Trim() }
                        };
                    }
                    return _json.Deserialize<Dictionary<string, object>>(stdout);
                }
            });
        }
    }

    public class MainWindow : Window
    {
        private readonly EngineBridge _bridge = new EngineBridge();
        private readonly List<Button> _navButtons = new List<Button>();
        private readonly Grid _contentHost = new Grid();
        private readonly Border[] _pages = new Border[5];

        private TextBlock _headerTitle;
        private TextBlock _viradaBadgeText;
        private Button _headerCta;
        private TextBlock _sidebarStatusText;
        private Ellipse _sidebarStatusDot;

        // Gerador state
        private string _selectedMode = "anti_colisao";
        private readonly List<Button> _modeButtons = new List<Button>();
        private Slider _sliderQtd;
        private TextBlock _lblQtdVal;
        private TextBox _txtMinSoma;
        private TextBox _txtMaxSoma;
        private readonly Border[] _gridBalls = new Border[60];
        private readonly TextBlock[] _gridBallTexts = new TextBlock[60];
        private TextBlock _kpiScore;
        private TextBlock _kpiMahalanobis;
        private TextBlock _kpiEntropia;
        private TextBlock _lblGenSummary;
        private StackPanel _ticketsListPanel;
        private List<List<int>> _currentGeneratedGames = new List<List<int>>();
        private bool _heatmapMode = false;
        private Button _btnHeatmap;
        private readonly Dictionary<int, int> _freqMap = new Dictionary<int, int>();
        private readonly Dictionary<int, int> _delayMap = new Dictionary<int, int>();
        private List<int> _lastHighlighted = new List<int>();

        // Fechamentos state
        private readonly HashSet<int> _poolSelected = new HashSet<int> { 4, 12, 19, 28, 35, 43, 51, 58, 10, 22 };
        private readonly Border[] _poolCells = new Border[60];
        private readonly TextBlock[] _poolCellTexts = new TextBlock[60];
        private string _garantia = "quadra";
        private Button _btnQuadra;
        private Button _btnQuina;
        private TextBlock _lblPoolCount;
        private TextBlock _lblFechSummary;
        private StackPanel _fechListPanel;
        private List<List<int>> _currentFechGames = new List<List<int>>();

        // Arbitragem & Bolao state
        private TextBox _txtPremio;
        private TextBox _txtOrcamento;
        private TextBlock _kpiArbStatus;
        private TextBlock _kpiArbValor;
        private TextBlock _kpiArbRoi;
        private TextBlock _txtArbDetail;

        // Conferencia state
        private TextBox _txtConfDezenas;
        private TextBlock _kpiQuadras;
        private TextBlock _kpiQuinas;
        private TextBlock _kpiSenas;
        private StackPanel _confDetailsPanel;

        // Dados Caixa state
        private TextBlock _txtSyncLog;
        private StackPanel _openContestsPanel;
        private Button _btnSync;

        private int _activeTab = 0;

        public MainWindow()
        {
            Title = "Cartela — Mathematical Lottery Intelligence Lab";
            Width = 1280;
            Height = 820;
            MinWidth = 1080;
            MinHeight = 700;
            WindowStartupLocation = WindowStartupLocation.CenterScreen;
            Background = Theme.BgCanvas;
            FontFamily = new FontFamily("Segoe UI Variable Text, Segoe UI");

            TryLoadIcon();
            ConfigureChrome();
            BuildShell();
            SwitchTab(0);
            Loaded += async (s, e) => await InitializeLiveAsync();
        }

        private void TryLoadIcon()
        {
            try
            {
                string[] paths = new[]
                {
                    System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "app_files", "assets", "cartela_logo.ico"),
                    System.IO.Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "..", "..", "assets", "cartela_logo.ico"),
                    @"app_files\assets\cartela_logo.ico"
                };
                foreach (string p in paths)
                {
                    string full = System.IO.Path.GetFullPath(p);
                    if (File.Exists(full))
                    {
                        Icon = BitmapFrame.Create(new Uri(full, UriKind.Absolute));
                        break;
                    }
                }
            }
            catch { }
        }

        private void ConfigureChrome()
        {
            var chrome = new WindowChrome
            {
                CaptionHeight = 44,
                CornerRadius = new CornerRadius(0),
                GlassFrameThickness = new Thickness(0),
                ResizeBorderThickness = new Thickness(6),
                UseAeroCaptionButtons = false
            };
            WindowChrome.SetWindowChrome(this, chrome);
        }

        private void BuildShell()
        {
            var root = new Grid { Background = Theme.BgCanvas };
            root.RowDefinitions.Add(new RowDefinition { Height = new GridLength(44) });
            root.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });

            // Top custom window bar
            var titleBar = new Grid { Background = Theme.BgSurface };
            titleBar.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            titleBar.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            var titleLeft = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(16, 0, 0, 0) };
            titleLeft.Children.Add(CreateMiniLogo(18));
            titleLeft.Children.Add(new TextBlock
            {
                Text = "Cartela — Mathematical Lottery Intelligence Lab",
                Foreground = Theme.TextSecondary,
                FontSize = 12,
                FontWeight = FontWeights.SemiBold,
                Margin = new Thickness(10, 0, 0, 0),
                VerticalAlignment = VerticalAlignment.Center
            });
            titleBar.Children.Add(titleLeft);

            var winBtns = new StackPanel { Orientation = Orientation.Horizontal };
            WindowChrome.SetIsHitTestVisibleInChrome(winBtns, true);
            winBtns.Children.Add(MakeCaptionBtn("—", (s, e) => WindowState = WindowState.Minimized, false));
            winBtns.Children.Add(MakeCaptionBtn("□", (s, e) => WindowState = WindowState == WindowState.Maximized ? WindowState.Normal : WindowState.Maximized, false));
            winBtns.Children.Add(MakeCaptionBtn("✕", (s, e) => Close(), true));
            Grid.SetColumn(winBtns, 1);
            titleBar.Children.Add(winBtns);

            var titleBorder = new Border { BorderBrush = Theme.Border, BorderThickness = new Thickness(0, 0, 0, 1), Child = titleBar };
            root.Children.Add(titleBorder);

            // Body: Sidebar + Main Area
            var body = new Grid();
            body.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(232) });
            body.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            Grid.SetRow(body, 1);
            root.Children.Add(body);

            // Sidebar
            var sidebar = BuildSidebar();
            body.Children.Add(sidebar);

            // Right Main Workspace
            var workspace = new Grid { Background = Theme.BgCanvas };
            workspace.RowDefinitions.Add(new RowDefinition { Height = new GridLength(76) });
            workspace.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
            Grid.SetColumn(workspace, 1);
            body.Children.Add(workspace);

            workspace.Children.Add(BuildTopHeader());

            _contentHost.Margin = new Thickness(28, 8, 28, 24);
            Grid.SetRow(_contentHost, 1);
            workspace.Children.Add(_contentHost);

            _pages[0] = BuildGeradorPage();
            _pages[1] = BuildFechamentosPage();
            _pages[2] = BuildArbitragemPage();
            _pages[3] = BuildConferenciaPage();
            _pages[4] = BuildDadosPage();

            foreach (var p in _pages)
            {
                p.Visibility = Visibility.Collapsed;
                _contentHost.Children.Add(p);
            }

            Content = root;
        }

        private Button MakeCaptionBtn(string text, RoutedEventHandler onClick, bool isClose)
        {
            var btn = new Button
            {
                Content = text,
                Width = 46,
                Height = 44,
                Background = Brushes.Transparent,
                Foreground = Theme.TextSecondary,
                BorderThickness = new Thickness(0),
                FontSize = 12,
                Cursor = Cursors.Hand
            };
            btn.MouseEnter += (s, e) =>
            {
                btn.Background = isClose ? Theme.Danger : Theme.BgMuted;
                btn.Foreground = isClose ? Brushes.White : Theme.TextPrimary;
            };
            btn.MouseLeave += (s, e) =>
            {
                btn.Background = Brushes.Transparent;
                btn.Foreground = Theme.TextSecondary;
            };
            btn.Click += onClick;
            return btn;
        }

        private UIElement CreateMiniLogo(double size)
        {
            var vb = new Viewbox { Width = size, Height = size };
            var canvas = new Canvas { Width = 64, Height = 64 };
            canvas.Children.Add(new Border
            {
                Width = 60,
                Height = 60,
                CornerRadius = new CornerRadius(14),
                Background = Theme.Brush("#0F172A"),
                BorderBrush = Theme.Brush("#334155"),
                BorderThickness = new Thickness(2)
            });
            Canvas.SetLeft(canvas.Children[0], 2);
            Canvas.SetTop(canvas.Children[0], 2);

            Action<double, double, SolidColorBrush, double> dot = (x, y, fill, r) =>
            {
                var el = new Ellipse { Width = r * 2, Height = r * 2, Fill = fill };
                Canvas.SetLeft(el, x - r);
                Canvas.SetTop(el, y - r);
                canvas.Children.Add(el);
            };
            dot(18, 24, Theme.Brush("#334155"), 5);
            dot(32, 24, Theme.Brush("#22C55E"), 5);
            dot(46, 24, Theme.Brush("#F59E0B"), 5.5);
            dot(18, 40, Theme.Brush("#22C55E"), 5);
            dot(32, 40, Theme.Brush("#334155"), 5);
            dot(46, 40, Theme.Brush("#22C55E"), 5);
            vb.Child = canvas;
            return vb;
        }

        private Border BuildSidebar()
        {
            var sideGrid = new Grid { Background = Theme.BgSurface };
            sideGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            sideGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });
            sideGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });

            // Brand header
            var brand = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(20, 22, 20, 24) };
            brand.Children.Add(CreateMiniLogo(36));
            var brandText = new StackPanel { Margin = new Thickness(12, 0, 0, 0), VerticalAlignment = VerticalAlignment.Center };
            brandText.Children.Add(new TextBlock { Text = "CARTELA", FontSize = 16, FontWeight = FontWeights.Bold, Foreground = Theme.TextPrimary });
            brandText.Children.Add(new TextBlock { Text = "QUANT LAB v2.0", FontSize = 10, FontWeight = FontWeights.SemiBold, Foreground = Theme.TextMuted });
            brand.Children.Add(brandText);
            sideGrid.Children.Add(brand);

            // Nav items
            var navPanel = new StackPanel { Margin = new Thickness(12, 0, 12, 0) };
            Grid.SetRow(navPanel, 1);
            var items = new[]
            {
                new { Title = "Gerador", Icon = "M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z" },
                new { Title = "Fechamentos", Icon = "M3 5h18M3 12h18M3 19h18M7 5v14M17 5v14" },
                new { Title = "Arbitragem", Icon = "M12 2v10l8.5 5A10 10 0 1 1 12 2z" },
                new { Title = "Conferência", Icon = "M9 12l2 2 4-4M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z" },
                new { Title = "Dados Caixa", Icon = "M4 6c0-1.7 3.6-3 8-3s8 1.3 8 3v12c0 1.7-3.6 3-8 3s-8-1.3-8-3V6zm0 6c0 1.7 3.6 3 8 3s8-1.3 8-3" }
            };
            for (int i = 0; i < items.Length; i++)
            {
                int idx = i;
                var btn = CreateNavButton(items[i].Title, items[i].Icon, idx);
                _navButtons.Add(btn);
                navPanel.Children.Add(btn);
            }
            sideGrid.Children.Add(navPanel);

            // Bottom live status pill
            var statusPill = new Border
            {
                Margin = new Thickness(14, 12, 14, 18),
                Padding = new Thickness(12, 10, 12, 10),
                Background = Theme.EmeraldLight,
                BorderBrush = Theme.Brush("#BBF7D0"),
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(10)
            };
            var statusRow = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            _sidebarStatusDot = new Ellipse { Width = 8, Height = 8, Fill = Theme.Emerald, VerticalAlignment = VerticalAlignment.Center };
            _sidebarStatusText = new TextBlock
            {
                Text = "Conectando Caixa...",
                Foreground = Theme.EmeraldDark,
                FontSize = 11.5,
                FontWeight = FontWeights.SemiBold,
                Margin = new Thickness(8, 0, 0, 0),
                TextTrimming = TextTrimming.CharacterEllipsis
            };
            statusRow.Children.Add(_sidebarStatusDot);
            statusRow.Children.Add(_sidebarStatusText);
            statusPill.Child = statusRow;
            Grid.SetRow(statusPill, 2);
            sideGrid.Children.Add(statusPill);

            return new Border { BorderBrush = Theme.Border, BorderThickness = new Thickness(0, 0, 1, 0), Child = sideGrid };
        }

        private Button CreateNavButton(string title, string pathData, int index)
        {
            var row = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            var icon = new System.Windows.Shapes.Path
            {
                Data = Geometry.Parse(pathData),
                Stroke = Theme.TextSecondary,
                StrokeThickness = 1.8,
                Width = 16,
                Height = 16,
                Stretch = Stretch.Uniform,
                VerticalAlignment = VerticalAlignment.Center
            };
            var lbl = new TextBlock
            {
                Text = title,
                FontSize = 13.5,
                FontWeight = FontWeights.Medium,
                Foreground = Theme.TextSecondary,
                Margin = new Thickness(12, 0, 0, 0),
                VerticalAlignment = VerticalAlignment.Center
            };
            row.Children.Add(icon);
            row.Children.Add(lbl);

            var btn = new Button
            {
                Content = row,
                HorizontalContentAlignment = HorizontalAlignment.Left,
                Padding = new Thickness(14, 11, 14, 11),
                Margin = new Thickness(0, 2, 0, 2),
                Background = Brushes.Transparent,
                BorderThickness = new Thickness(0),
                Cursor = Cursors.Hand,
                Tag = new object[] { icon, lbl }
            };
            var template = new ControlTemplate(typeof(Button));
            var bd = new FrameworkElementFactory(typeof(Border));
            bd.SetValue(Border.BackgroundProperty, new TemplateBindingExtension(Button.BackgroundProperty));
            bd.SetValue(Border.CornerRadiusProperty, new CornerRadius(10));
            bd.SetValue(Border.PaddingProperty, new TemplateBindingExtension(Button.PaddingProperty));
            var cp = new FrameworkElementFactory(typeof(ContentPresenter));
            bd.AppendChild(cp);
            template.VisualTree = bd;
            btn.Template = template;

            btn.MouseEnter += (s, e) => { if (_activeTab != index) btn.Background = Theme.BgMuted; };
            btn.MouseLeave += (s, e) => { if (_activeTab != index) btn.Background = Brushes.Transparent; };
            btn.Click += (s, e) => SwitchTab(index);
            return btn;
        }

        private Grid BuildTopHeader()
        {
            var header = new Grid { Margin = new Thickness(28, 16, 28, 8) };
            header.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            header.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });

            _headerTitle = new TextBlock
            {
                Text = "Gerador Inteligente",
                FontSize = 24,
                FontWeight = FontWeights.Bold,
                Foreground = Theme.TextPrimary,
                VerticalAlignment = VerticalAlignment.Center
            };
            header.Children.Add(_headerTitle);

            var right = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            var viradaPill = new Border
            {
                Background = Theme.GoldLight,
                BorderBrush = Theme.GoldBorder,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(18),
                Padding = new Thickness(14, 7, 14, 7),
                Margin = new Thickness(0, 0, 12, 0),
                VerticalAlignment = VerticalAlignment.Center
            };
            _viradaBadgeText = new TextBlock
            {
                Text = "Mega da Virada • Carregando...",
                Foreground = Theme.GoldText,
                FontSize = 12,
                FontWeight = FontWeights.SemiBold
            };
            viradaPill.Child = _viradaBadgeText;
            right.Children.Add(viradaPill);

            _headerCta = CreatePrimaryButton("Gerar Jogos", async (s, e) => await ExecuteHeaderCtaAsync());
            right.Children.Add(_headerCta);
            Grid.SetColumn(right, 1);
            header.Children.Add(right);
            return header;
        }

        private Button CreatePrimaryButton(string text, RoutedEventHandler onClick)
        {
            var btn = new Button
            {
                Content = text,
                Background = Theme.Emerald,
                Foreground = Brushes.White,
                FontSize = 13,
                FontWeight = FontWeights.SemiBold,
                Padding = new Thickness(18, 10, 18, 10),
                BorderThickness = new Thickness(0),
                Cursor = Cursors.Hand
            };
            var template = new ControlTemplate(typeof(Button));
            var bd = new FrameworkElementFactory(typeof(Border));
            bd.SetValue(Border.BackgroundProperty, new TemplateBindingExtension(Button.BackgroundProperty));
            bd.SetValue(Border.CornerRadiusProperty, new CornerRadius(10));
            bd.SetValue(Border.PaddingProperty, new TemplateBindingExtension(Button.PaddingProperty));
            var cp = new FrameworkElementFactory(typeof(ContentPresenter));
            cp.SetValue(FrameworkElement.HorizontalAlignmentProperty, HorizontalAlignment.Center);
            cp.SetValue(FrameworkElement.VerticalAlignmentProperty, VerticalAlignment.Center);
            bd.AppendChild(cp);
            template.VisualTree = bd;
            btn.Template = template;
            btn.MouseEnter += (s, e) => btn.Background = Theme.EmeraldDark;
            btn.MouseLeave += (s, e) => btn.Background = Theme.Emerald;
            btn.Click += onClick;
            return btn;
        }

        private Button CreateSecondaryButton(string text, RoutedEventHandler onClick)
        {
            var btn = new Button
            {
                Content = text,
                Background = Theme.BgSurface,
                Foreground = Theme.TextPrimary,
                FontSize = 12.5,
                FontWeight = FontWeights.SemiBold,
                Padding = new Thickness(14, 8, 14, 8),
                BorderBrush = Theme.BorderStrong,
                BorderThickness = new Thickness(1),
                Cursor = Cursors.Hand
            };
            var template = new ControlTemplate(typeof(Button));
            var bd = new FrameworkElementFactory(typeof(Border));
            bd.SetValue(Border.BackgroundProperty, new TemplateBindingExtension(Button.BackgroundProperty));
            bd.SetValue(Border.BorderBrushProperty, new TemplateBindingExtension(Button.BorderBrushProperty));
            bd.SetValue(Border.BorderThicknessProperty, new TemplateBindingExtension(Button.BorderThicknessProperty));
            bd.SetValue(Border.CornerRadiusProperty, new CornerRadius(9));
            bd.SetValue(Border.PaddingProperty, new TemplateBindingExtension(Button.PaddingProperty));
            var cp = new FrameworkElementFactory(typeof(ContentPresenter));
            cp.SetValue(FrameworkElement.HorizontalAlignmentProperty, HorizontalAlignment.Center);
            cp.SetValue(FrameworkElement.VerticalAlignmentProperty, VerticalAlignment.Center);
            bd.AppendChild(cp);
            template.VisualTree = bd;
            btn.Template = template;
            btn.MouseEnter += (s, e) => btn.Background = Theme.BgMuted;
            btn.MouseLeave += (s, e) => btn.Background = Theme.BgSurface;
            btn.Click += onClick;
            return btn;
        }

        private Border MakeCard(UIElement child, Thickness? padding = null)
        {
            return new Border
            {
                Background = Theme.BgSurface,
                BorderBrush = Theme.Border,
                BorderThickness = new Thickness(1),
                CornerRadius = new CornerRadius(14),
                Padding = padding ?? new Thickness(20),
                Effect = Theme.CardShadow(),
                Child = child
            };
        }

        private Border MakeKpiCard(string title, out TextBlock valueLabel, SolidColorBrush accentColor)
        {
            var sp = new StackPanel();
            sp.Children.Add(new TextBlock
            {
                Text = title.ToUpperInvariant(),
                Foreground = Theme.TextMuted,
                FontSize = 10.5,
                FontWeight = FontWeights.Bold
            });
            valueLabel = new TextBlock
            {
                Text = "--",
                Foreground = accentColor,
                FontSize = 24,
                FontWeight = FontWeights.Bold,
                Margin = new Thickness(0, 6, 0, 0)
            };
            sp.Children.Add(valueLabel);
            return MakeCard(sp, new Thickness(18, 14, 18, 14));
        }

        // -----------------------------------------------------------------
        // PAGE 0: GERADOR INTELIGENTE
        // -----------------------------------------------------------------
        private Border BuildGeradorPage()
        {
            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1.05, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(20) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1.15, GridUnitType.Star) });

            // Left column: Config + 10x6 Volante Grid
            var leftStack = new StackPanel();

            var cfgPanel = new StackPanel();
            // Segmented mode pills
            var modeWrap = new Border
            {
                Background = Theme.BgMuted,
                CornerRadius = new CornerRadius(10),
                Padding = new Thickness(4),
                Margin = new Thickness(0, 0, 0, 14)
            };
            var modeGrid = new UniformGrid { Columns = 5 };
            var modes = new[]
            {
                new { Key = "balanceado", Label = "★ Balanceado V2" },
                new { Key = "anti_colisao", Label = "Anti-Colisão" },
                new { Key = "mahalanobis", Label = "Mahalanobis" },
                new { Key = "frequencia", Label = "Frequência" },
                new { Key = "aleatorio", Label = "Aleatório" }
            };
            foreach (var m in modes)
            {
                string key = m.Key;
                var b = new Button
                {
                    Content = m.Label,
                    Padding = new Thickness(8, 8, 8, 8),
                    FontSize = 12,
                    FontWeight = FontWeights.SemiBold,
                    BorderThickness = new Thickness(0),
                    Cursor = Cursors.Hand,
                    Tag = key
                };
                var tpl = new ControlTemplate(typeof(Button));
                var bdr = new FrameworkElementFactory(typeof(Border));
                bdr.SetValue(Border.BackgroundProperty, new TemplateBindingExtension(Button.BackgroundProperty));
                bdr.SetValue(Border.CornerRadiusProperty, new CornerRadius(8));
                bdr.SetValue(Border.PaddingProperty, new TemplateBindingExtension(Button.PaddingProperty));
                var cp = new FrameworkElementFactory(typeof(ContentPresenter));
                cp.SetValue(FrameworkElement.HorizontalAlignmentProperty, HorizontalAlignment.Center);
                bdr.AppendChild(cp);
                tpl.VisualTree = bdr;
                b.Template = tpl;
                b.Click += (s, e) => SelectMode(key);
                _modeButtons.Add(b);
                modeGrid.Children.Add(b);
            }
            modeWrap.Child = modeGrid;
            cfgPanel.Children.Add(modeWrap);
            SelectMode("anti_colisao");

            // Quantity & Sum filters
            var qtdRow = new Grid { Margin = new Thickness(0, 0, 0, 10) };
            qtdRow.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            qtdRow.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            qtdRow.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            qtdRow.Children.Add(new TextBlock { Text = "Quantidade de Jogos:", Foreground = Theme.TextSecondary, FontSize = 12.5, VerticalAlignment = VerticalAlignment.Center });
            _sliderQtd = new Slider { Minimum = 1, Maximum = 30, Value = 8, IsSnapToTickEnabled = true, TickFrequency = 1, Margin = new Thickness(12, 0, 12, 0), VerticalAlignment = VerticalAlignment.Center };
            Grid.SetColumn(_sliderQtd, 1);
            qtdRow.Children.Add(_sliderQtd);
            _lblQtdVal = new TextBlock { Text = "8", Foreground = Theme.Emerald, FontSize = 14, FontWeight = FontWeights.Bold, VerticalAlignment = VerticalAlignment.Center };
            Grid.SetColumn(_lblQtdVal, 2);
            qtdRow.Children.Add(_lblQtdVal);
            _sliderQtd.ValueChanged += (s, e) => _lblQtdVal.Text = ((int)_sliderQtd.Value).ToString();
            cfgPanel.Children.Add(qtdRow);

            var sumRow = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            sumRow.Children.Add(new TextBlock { Text = "Filtro Soma Gaussiana:", Foreground = Theme.TextSecondary, FontSize = 12.5, VerticalAlignment = VerticalAlignment.Center });
            _txtMinSoma = MakeInputBox("140", 56);
            _txtMinSoma.Margin = new Thickness(10, 0, 6, 0);
            sumRow.Children.Add(_txtMinSoma);
            sumRow.Children.Add(new TextBlock { Text = "a", Foreground = Theme.TextMuted, VerticalAlignment = VerticalAlignment.Center });
            _txtMaxSoma = MakeInputBox("225", 56);
            _txtMaxSoma.Margin = new Thickness(6, 0, 0, 0);
            sumRow.Children.Add(_txtMaxSoma);
            cfgPanel.Children.Add(sumRow);

            leftStack.Children.Add(MakeCard(cfgPanel, new Thickness(18)));

            // 10x6 Volante Preview Grid
            var volantePanel = new StackPanel();
            var volHdr = new Grid { Margin = new Thickness(0, 0, 0, 12) };
            volHdr.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            volHdr.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            volHdr.Children.Add(new TextBlock
            {
                Text = "Volante Oficial (01 – 60) • Clique em um jogo para destacar",
                Foreground = Theme.TextMuted,
                FontSize = 11.5,
                FontWeight = FontWeights.SemiBold,
                VerticalAlignment = VerticalAlignment.Center
            });
            _btnHeatmap = CreateSecondaryButton("Mapa de Calor", async (s, e) => await ToggleHeatmapAsync());
            Grid.SetColumn(_btnHeatmap, 1);
            volHdr.Children.Add(_btnHeatmap);
            volantePanel.Children.Add(volHdr);
            var grid10x6 = new UniformGrid { Columns = 10, Rows = 6 };
            for (int i = 0; i < 60; i++)
            {
                var txt = new TextBlock
                {
                    Text = (i + 1).ToString("00"),
                    FontSize = 12,
                    FontWeight = FontWeights.SemiBold,
                    Foreground = Theme.TextSecondary,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center
                };
                var cell = new Border
                {
                    Height = 38,
                    Margin = new Thickness(3),
                    CornerRadius = new CornerRadius(19),
                    Background = Theme.BgMuted,
                    BorderBrush = Theme.Border,
                    BorderThickness = new Thickness(1),
                    Child = txt
                };
                _gridBalls[i] = cell;
                _gridBallTexts[i] = txt;
                grid10x6.Children.Add(cell);
            }
            volantePanel.Children.Add(grid10x6);
            var volanteCard = MakeCard(volantePanel, new Thickness(18));
            volanteCard.Margin = new Thickness(0, 16, 0, 0);
            leftStack.Children.Add(volanteCard);

            grid.Children.Add(leftStack);

            // Right column: 3 KPIs + Generated Tickets Card
            var rightGrid = new Grid();
            rightGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            rightGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(16) });
            rightGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });

            var kpiGrid = new UniformGrid { Columns = 3 };
            var k1 = MakeKpiCard("Anti-Colisão Médio", out _kpiScore, Theme.Emerald);
            k1.Margin = new Thickness(0, 0, 6, 0);
            var k2 = MakeKpiCard("Mahalanobis (Dm)", out _kpiMahalanobis, Theme.TextPrimary);
            k2.Margin = new Thickness(3, 0, 3, 0);
            var k3 = MakeKpiCard("Entropia Shannon", out _kpiEntropia, Theme.Blue);
            k3.Margin = new Thickness(6, 0, 0, 0);
            kpiGrid.Children.Add(k1);
            kpiGrid.Children.Add(k2);
            kpiGrid.Children.Add(k3);
            rightGrid.Children.Add(kpiGrid);

            var listCardGrid = new Grid();
            listCardGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            listCardGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });

            var listHdr = new Grid { Margin = new Thickness(0, 0, 0, 12) };
            listHdr.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            listHdr.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            _lblGenSummary = new TextBlock
            {
                Text = "Jogos Gerados",
                Foreground = Theme.TextPrimary,
                FontSize = 14,
                FontWeight = FontWeights.Bold,
                VerticalAlignment = VerticalAlignment.Center
            };
            listHdr.Children.Add(_lblGenSummary);
            var expRow = new StackPanel { Orientation = Orientation.Horizontal };
            expRow.Children.Add(CreateSecondaryButton("Copiar", (s, e) => CopyGames(_currentGeneratedGames)));
            var btnCsv = CreateSecondaryButton("CSV", async (s, e) => await ExportGamesAsync("export_csv", "csv", _currentGeneratedGames));
            btnCsv.Margin = new Thickness(6, 0, 6, 0);
            expRow.Children.Add(btnCsv);
            expRow.Children.Add(CreateSecondaryButton("PDF", async (s, e) => await ExportGamesAsync("export_pdf", "pdf", _currentGeneratedGames)));
            Grid.SetColumn(expRow, 1);
            listHdr.Children.Add(expRow);
            listCardGrid.Children.Add(listHdr);

            _ticketsListPanel = new StackPanel();
            var scroll = new ScrollViewer { VerticalScrollBarVisibility = ScrollBarVisibility.Auto, Content = _ticketsListPanel };
            Grid.SetRow(scroll, 1);
            listCardGrid.Children.Add(scroll);

            var listCard = MakeCard(listCardGrid, new Thickness(18));
            Grid.SetRow(listCard, 2);
            rightGrid.Children.Add(listCard);

            Grid.SetColumn(rightGrid, 2);
            grid.Children.Add(rightGrid);

            return new Border { Child = grid };
        }

        private void SelectMode(string mode)
        {
            _selectedMode = mode;
            foreach (var b in _modeButtons)
            {
                bool active = (string)b.Tag == mode;
                b.Background = active ? Theme.BgSurface : Brushes.Transparent;
                b.Foreground = active ? Theme.EmeraldDark : Theme.TextSecondary;
            }
        }

        private void HighlightVolante(List<int> dezenas)
        {
            _lastHighlighted = dezenas ?? new List<int>();
            var set = new HashSet<int>(_lastHighlighted);
            if (_heatmapMode && _freqMap.Count == 60)
            {
                int minF = _freqMap.Values.Min();
                int maxF = Math.Max(minF + 1, _freqMap.Values.Max());
                for (int i = 0; i < 60; i++)
                {
                    int num = i + 1;
                    int f = _freqMap[num];
                    int d = _delayMap.ContainsKey(num) ? _delayMap[num] : 0;
                    double ratio = (double)(f - minF) / (maxF - minF);
                    if (ratio >= 0.72)
                    {
                        _gridBalls[i].Background = Theme.GoldLight;
                        _gridBalls[i].BorderBrush = Theme.GoldBorder;
                        _gridBallTexts[i].Foreground = Theme.GoldText;
                    }
                    else if (ratio >= 0.38)
                    {
                        _gridBalls[i].Background = Theme.EmeraldLight;
                        _gridBalls[i].BorderBrush = Theme.Brush("#86EFAC");
                        _gridBallTexts[i].Foreground = Theme.EmeraldDark;
                    }
                    else
                    {
                        _gridBalls[i].Background = Theme.BlueLight;
                        _gridBalls[i].BorderBrush = Theme.Brush("#BAE6FD");
                        _gridBallTexts[i].Foreground = Theme.Blue;
                    }
                    _gridBalls[i].ToolTip = string.Format("Dezena {0:00} • {1} sorteios • Atraso: {2} conc.", num, f, d);
                }
                return;
            }
            for (int i = 0; i < 60; i++)
            {
                bool on = set.Contains(i + 1);
                _gridBalls[i].Background = on ? Theme.Emerald : Theme.BgMuted;
                _gridBalls[i].BorderBrush = on ? Theme.EmeraldDark : Theme.Border;
                _gridBallTexts[i].Foreground = on ? Brushes.White : Theme.TextSecondary;
                _gridBalls[i].ToolTip = null;
            }
        }

        private async Task ToggleHeatmapAsync()
        {
            _heatmapMode = !_heatmapMode;
            _btnHeatmap.Background = _heatmapMode ? Theme.GoldLight : Theme.BgSurface;
            _btnHeatmap.BorderBrush = _heatmapMode ? Theme.GoldBorder : Theme.BorderStrong;
            _btnHeatmap.Foreground = _heatmapMode ? Theme.GoldText : Theme.TextPrimary;
            if (_heatmapMode && _freqMap.Count < 60)
            {
                var res = await _bridge.CallAsync("heatmap");
                if (res.ContainsKey("ok") && Convert.ToBoolean(res["ok"]))
                {
                    var freqs = res["frequencias"] as Dictionary<string, object>;
                    var atrasos = res["atrasos"] as Dictionary<string, object>;
                    if (freqs != null)
                    {
                        foreach (var kv in freqs) _freqMap[int.Parse(kv.Key)] = Convert.ToInt32(kv.Value);
                    }
                    if (atrasos != null)
                    {
                        foreach (var kv in atrasos) _delayMap[int.Parse(kv.Key)] = Convert.ToInt32(kv.Value);
                    }
                }
            }
            HighlightVolante(_lastHighlighted);
        }

        private UIElement CreateTicketRow(int idx, List<int> dezenas, int soma, double score, bool clickableForVolante)
        {
            var row = new Grid();
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(36) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(60) });
            row.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(60) });

            row.Children.Add(new TextBlock
            {
                Text = "#" + idx.ToString("00"),
                Foreground = Theme.TextMuted,
                FontSize = 12,
                FontWeight = FontWeights.SemiBold,
                VerticalAlignment = VerticalAlignment.Center
            });

            var balls = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            for (int k = 0; k < dezenas.Count; k++)
            {
                bool isHigh = dezenas[k] > 31;
                var ball = new Border
                {
                    Width = 30,
                    Height = 30,
                    CornerRadius = new CornerRadius(15),
                    Margin = new Thickness(0, 0, 6, 0),
                    Background = isHigh ? Theme.EmeraldLight : Theme.GoldLight,
                    BorderBrush = isHigh ? Theme.Brush("#86EFAC") : Theme.GoldBorder,
                    BorderThickness = new Thickness(1),
                    Child = new TextBlock
                    {
                        Text = dezenas[k].ToString("00"),
                        Foreground = isHigh ? Theme.EmeraldDark : Theme.GoldText,
                        FontSize = 12,
                        FontWeight = FontWeights.Bold,
                        HorizontalAlignment = HorizontalAlignment.Center,
                        VerticalAlignment = VerticalAlignment.Center
                    }
                };
                balls.Children.Add(ball);
            }
            Grid.SetColumn(balls, 1);
            row.Children.Add(balls);

            var lblSum = new TextBlock
            {
                Text = "Σ " + soma,
                Foreground = Theme.TextSecondary,
                FontSize = 12,
                FontWeight = FontWeights.SemiBold,
                VerticalAlignment = VerticalAlignment.Center
            };
            Grid.SetColumn(lblSum, 2);
            row.Children.Add(lblSum);

            var lblScore = new TextBlock
            {
                Text = score.ToString("0") + "%",
                Foreground = Theme.EmeraldDark,
                FontSize = 12.5,
                FontWeight = FontWeights.Bold,
                VerticalAlignment = VerticalAlignment.Center,
                HorizontalAlignment = HorizontalAlignment.Right
            };
            Grid.SetColumn(lblScore, 3);
            row.Children.Add(lblScore);

            var card = new Border
            {
                Padding = new Thickness(12, 8, 12, 8),
                Margin = new Thickness(0, 0, 0, 6),
                CornerRadius = new CornerRadius(10),
                Background = Theme.BgCanvas,
                BorderBrush = Theme.Border,
                BorderThickness = new Thickness(1),
                Cursor = clickableForVolante ? Cursors.Hand : Cursors.Arrow,
                Child = row
            };
            if (clickableForVolante)
            {
                card.MouseEnter += (s, e) => card.Background = Theme.BgMuted;
                card.MouseLeave += (s, e) => card.Background = Theme.BgCanvas;
                card.MouseLeftButtonUp += (s, e) => HighlightVolante(dezenas);
            }
            return card;
        }

        // -----------------------------------------------------------------
        // PAGE 1: FECHAMENTOS COMBINATÓRIOS C(v,k,t)
        // -----------------------------------------------------------------
        private Border BuildFechamentosPage()
        {
            var grid = new Grid();
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1.05, GridUnitType.Star) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(20) });
            grid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1.15, GridUnitType.Star) });

            var left = new StackPanel();
            var poolHeader = new Grid { Margin = new Thickness(0, 0, 0, 12) };
            poolHeader.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            poolHeader.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            _lblPoolCount = new TextBlock
            {
                Text = "Pool Selecionado: 10 dezenas (C# /unsafe Kernel)",
                Foreground = Theme.TextPrimary,
                FontSize = 13.5,
                FontWeight = FontWeights.Bold,
                VerticalAlignment = VerticalAlignment.Center
            };
            poolHeader.Children.Add(_lblPoolCount);
            var clearBtn = CreateSecondaryButton("Limpar", (s, e) => { _poolSelected.Clear(); RefreshPoolGrid(); });
            Grid.SetColumn(clearBtn, 1);
            poolHeader.Children.Add(clearBtn);
            left.Children.Add(poolHeader);

            var grid10x6 = new UniformGrid { Columns = 10, Rows = 6 };
            for (int i = 0; i < 60; i++)
            {
                int num = i + 1;
                var txt = new TextBlock
                {
                    Text = num.ToString("00"),
                    FontSize = 12,
                    FontWeight = FontWeights.SemiBold,
                    HorizontalAlignment = HorizontalAlignment.Center,
                    VerticalAlignment = VerticalAlignment.Center
                };
                var cell = new Border
                {
                    Height = 38,
                    Margin = new Thickness(3),
                    CornerRadius = new CornerRadius(19),
                    BorderThickness = new Thickness(1),
                    Cursor = Cursors.Hand,
                    Child = txt
                };
                cell.MouseLeftButtonUp += (s, e) =>
                {
                    if (_poolSelected.Contains(num)) _poolSelected.Remove(num);
                    else if (_poolSelected.Count < 16) _poolSelected.Add(num);
                    RefreshPoolGrid();
                };
                _poolCells[i] = cell;
                _poolCellTexts[i] = txt;
                grid10x6.Children.Add(cell);
            }
            left.Children.Add(grid10x6);

            var garRow = new StackPanel { Orientation = Orientation.Horizontal, Margin = new Thickness(0, 16, 0, 0) };
            garRow.Children.Add(new TextBlock { Text = "Garantia Matemática:", Foreground = Theme.TextSecondary, FontSize = 12.5, VerticalAlignment = VerticalAlignment.Center, Margin = new Thickness(0, 0, 12, 0) });
            _btnQuadra = CreateSecondaryButton("Quadra (t=4)", (s, e) => { _garantia = "quadra"; RefreshGarantiaBtns(); });
            _btnQuina = CreateSecondaryButton("Quina (t=5)", (s, e) => { _garantia = "quina"; RefreshGarantiaBtns(); });
            _btnQuina.Margin = new Thickness(8, 0, 0, 0);
            garRow.Children.Add(_btnQuadra);
            garRow.Children.Add(_btnQuina);
            left.Children.Add(garRow);
            RefreshPoolGrid();
            RefreshGarantiaBtns();

            grid.Children.Add(MakeCard(left, new Thickness(20)));

            // Right: result matrix
            var rightGrid = new Grid();
            rightGrid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            rightGrid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });

            var hdr = new Grid { Margin = new Thickness(0, 0, 0, 12) };
            hdr.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            hdr.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            _lblFechSummary = new TextBlock
            {
                Text = "Selecione de 6 a 16 dezenas e clique em Calcular Fechamento.",
                Foreground = Theme.TextSecondary,
                FontSize = 12.5,
                FontWeight = FontWeights.SemiBold,
                TextWrapping = TextWrapping.Wrap,
                VerticalAlignment = VerticalAlignment.Center
            };
            hdr.Children.Add(_lblFechSummary);
            var btnPdf = CreateSecondaryButton("Exportar PDF", async (s, e) => await ExportGamesAsync("export_pdf", "pdf", _currentFechGames));
            Grid.SetColumn(btnPdf, 1);
            hdr.Children.Add(btnPdf);
            rightGrid.Children.Add(hdr);

            _fechListPanel = new StackPanel();
            var scroll = new ScrollViewer { VerticalScrollBarVisibility = ScrollBarVisibility.Auto, Content = _fechListPanel };
            Grid.SetRow(scroll, 1);
            rightGrid.Children.Add(scroll);

            var rightCard = MakeCard(rightGrid, new Thickness(20));
            Grid.SetColumn(rightCard, 2);
            grid.Children.Add(rightCard);

            return new Border { Child = grid };
        }

        private void RefreshPoolGrid()
        {
            for (int i = 0; i < 60; i++)
            {
                bool on = _poolSelected.Contains(i + 1);
                _poolCells[i].Background = on ? Theme.Emerald : Theme.BgMuted;
                _poolCells[i].BorderBrush = on ? Theme.EmeraldDark : Theme.Border;
                _poolCellTexts[i].Foreground = on ? Brushes.White : Theme.TextSecondary;
            }
            _lblPoolCount.Text = string.Format("Pool Selecionado: {0} dezenas (máx. 16)", _poolSelected.Count);
        }

        private void RefreshGarantiaBtns()
        {
            bool q4 = _garantia == "quadra";
            _btnQuadra.Background = q4 ? Theme.EmeraldLight : Theme.BgSurface;
            _btnQuadra.BorderBrush = q4 ? Theme.Emerald : Theme.BorderStrong;
            _btnQuadra.Foreground = q4 ? Theme.EmeraldDark : Theme.TextSecondary;

            _btnQuina.Background = !q4 ? Theme.EmeraldLight : Theme.BgSurface;
            _btnQuina.BorderBrush = !q4 ? Theme.Emerald : Theme.BorderStrong;
            _btnQuina.Foreground = !q4 ? Theme.EmeraldDark : Theme.TextSecondary;
        }

        // -----------------------------------------------------------------
        // PAGE 2: RADAR DE ARBITRAGEM E[X]
        // -----------------------------------------------------------------
        private Border BuildArbitragemPage()
        {
            var stack = new StackPanel();

            var top = new StackPanel();
            top.Children.Add(new TextBlock
            {
                Text = "Radar de Arbitragem Financeira (Modelo Joan Ginther)",
                FontSize = 15,
                FontWeight = FontWeights.Bold,
                Foreground = Theme.TextPrimary
            });
            top.Children.Add(new TextBlock
            {
                Text = "Identifica janelas em que o Valor Esperado E[X] supera o custo do bilhete (ex.: Mega da Virada).",
                FontSize = 12.5,
                Foreground = Theme.TextMuted,
                Margin = new Thickness(0, 4, 0, 14)
            });

            var inRow = new StackPanel { Orientation = Orientation.Horizontal, VerticalAlignment = VerticalAlignment.Center };
            inRow.Children.Add(new TextBlock { Text = "Prêmio Estimado (R$):", Foreground = Theme.TextSecondary, FontSize = 13, VerticalAlignment = VerticalAlignment.Center });
            _txtPremio = MakeInputBox("1000000000", 150);
            _txtPremio.Margin = new Thickness(10, 0, 10, 0);
            inRow.Children.Add(_txtPremio);
            var btnVirada = CreateSecondaryButton("Mega da Virada (Ao Vivo)", async (s, e) => await LoadLiveViradaIntoArbitragemAsync());
            btnVirada.Margin = new Thickness(0, 0, 16, 0);
            inRow.Children.Add(btnVirada);
            inRow.Children.Add(new TextBlock { Text = "Orçamento Bolão (R$):", Foreground = Theme.TextSecondary, FontSize = 13, VerticalAlignment = VerticalAlignment.Center });
            _txtOrcamento = MakeInputBox("150", 80);
            _txtOrcamento.Margin = new Thickness(8, 0, 8, 0);
            inRow.Children.Add(_txtOrcamento);
            var btnBolao = CreateSecondaryButton("Planejar Bolão Ótimo", async (s, e) => await RunBolaoAsync());
            btnBolao.Margin = new Thickness(0, 0, 8, 0);
            inRow.Children.Add(btnBolao);
            inRow.Children.Add(CreateSecondaryButton("Simular 100k Sorteios (C#)", async (s, e) => await RunMonteCarloAsync()));
            top.Children.Add(inRow);
            stack.Children.Add(MakeCard(top, new Thickness(20)));

            var kpiGrid = new UniformGrid { Columns = 3, Margin = new Thickness(0, 16, 0, 16) };
            var c1 = MakeKpiCard("Diretriz Matemática", out _kpiArbStatus, Theme.Emerald);
            c1.Margin = new Thickness(0, 0, 8, 0);
            var c2 = MakeKpiCard("Valor Intrínseco / Bilhete", out _kpiArbValor, Theme.TextPrimary);
            c2.Margin = new Thickness(4, 0, 4, 0);
            var c3 = MakeKpiCard("ROI Esperado", out _kpiArbRoi, Theme.Gold);
            c3.Margin = new Thickness(8, 0, 0, 0);
            kpiGrid.Children.Add(c1);
            kpiGrid.Children.Add(c2);
            kpiGrid.Children.Add(c3);
            stack.Children.Add(kpiGrid);

            var detailPanel = new StackPanel();
            detailPanel.Children.Add(new TextBlock { Text = "Diagnóstico Analítico do Concurso", FontSize = 14, FontWeight = FontWeights.Bold, Foreground = Theme.TextPrimary, Margin = new Thickness(0, 0, 0, 10) });
            _txtArbDetail = new TextBlock { Text = "Clique em Calcular Arbitragem para analisar o concurso.", Foreground = Theme.TextSecondary, FontSize = 13, TextWrapping = TextWrapping.Wrap, LineHeight = 22 };
            detailPanel.Children.Add(_txtArbDetail);
            stack.Children.Add(MakeCard(detailPanel, new Thickness(20)));

            return new Border { Child = stack };
        }

        // -----------------------------------------------------------------
        // PAGE 3: CONFERÊNCIA HISTÓRICA
        // -----------------------------------------------------------------
        private Border BuildConferenciaPage()
        {
            var grid = new Grid();
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(16) });
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(16) });
            grid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });

            var top = new StackPanel();
            top.Children.Add(new TextBlock { Text = "Conferência Histórica (Backtest 64-bit Bitmask)", FontSize = 15, FontWeight = FontWeights.Bold, Foreground = Theme.TextPrimary });
            top.Children.Add(new TextBlock { Text = "Digite 6 dezenas separadas por espaço ou vírgula para conferir contra toda a base oficial da Caixa.", FontSize = 12.5, Foreground = Theme.TextMuted, Margin = new Thickness(0, 4, 0, 12) });
            var confRow = new StackPanel { Orientation = Orientation.Horizontal };
            _txtConfDezenas = MakeInputBox("04 12 19 28 35 43", 320);
            _txtConfDezenas.KeyDown += async (s, e) => { if (e.Key == Key.Enter) await RunBacktestAsync(); };
            confRow.Children.Add(_txtConfDezenas);
            var btnConf = CreatePrimaryButton("Conferir", async (s, e) => await RunBacktestAsync());
            btnConf.Margin = new Thickness(12, 0, 0, 0);
            confRow.Children.Add(btnConf);
            top.Children.Add(confRow);
            grid.Children.Add(MakeCard(top, new Thickness(20)));

            var kpiGrid = new UniformGrid { Columns = 3 };
            var k1 = MakeKpiCard("Quadras (4 Acertos)", out _kpiQuadras, Theme.Blue);
            k1.Margin = new Thickness(0, 0, 8, 0);
            var k2 = MakeKpiCard("Quinas (5 Acertos)", out _kpiQuinas, Theme.Gold);
            k2.Margin = new Thickness(4, 0, 4, 0);
            var k3 = MakeKpiCard("Senas (6 Acertos)", out _kpiSenas, Theme.Emerald);
            k3.Margin = new Thickness(8, 0, 0, 0);
            kpiGrid.Children.Add(k1);
            kpiGrid.Children.Add(k2);
            kpiGrid.Children.Add(k3);
            Grid.SetRow(kpiGrid, 2);
            grid.Children.Add(kpiGrid);

            _confDetailsPanel = new StackPanel();
            var scroll = new ScrollViewer { VerticalScrollBarVisibility = ScrollBarVisibility.Auto, Content = _confDetailsPanel };
            var detCard = MakeCard(scroll, new Thickness(20));
            Grid.SetRow(detCard, 4);
            grid.Children.Add(detCard);

            return new Border { Child = grid };
        }

        // -----------------------------------------------------------------
        // PAGE 4: DADOS OFICIAIS CAIXA
        // -----------------------------------------------------------------
        private Border BuildDadosPage()
        {
            var grid = new Grid();
            grid.RowDefinitions.Add(new RowDefinition { Height = GridLength.Auto });
            grid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(16) });
            grid.RowDefinitions.Add(new RowDefinition { Height = new GridLength(1, GridUnitType.Star) });

            var topGrid = new Grid();
            topGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            topGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = GridLength.Auto });
            var info = new StackPanel();
            info.Children.Add(new TextBlock { Text = "Sincronização Oficial (servicebus3 + Loterias Online)", FontSize = 15, FontWeight = FontWeights.Bold, Foreground = Theme.TextPrimary });
            info.Children.Add(new TextBlock { Text = "Baixa automaticamente o histórico em lote (.xlsx) e os parâmetros ao vivo da Mega da Virada.", FontSize = 12.5, Foreground = Theme.TextMuted, Margin = new Thickness(0, 4, 0, 0) });
            topGrid.Children.Add(info);
            _btnSync = CreatePrimaryButton("Sincronizar Agora", async (s, e) => await RunSyncAsync());
            Grid.SetColumn(_btnSync, 1);
            topGrid.Children.Add(_btnSync);
            grid.Children.Add(MakeCard(topGrid, new Thickness(20)));

            var bodyGrid = new Grid();
            bodyGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            bodyGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(16) });
            bodyGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });

            var contestsWrap = new StackPanel();
            contestsWrap.Children.Add(new TextBlock { Text = "Concursos Abertos Ao Vivo", FontSize = 14, FontWeight = FontWeights.Bold, Foreground = Theme.TextPrimary, Margin = new Thickness(0, 0, 0, 10) });
            _openContestsPanel = new StackPanel();
            contestsWrap.Children.Add(_openContestsPanel);
            bodyGrid.Children.Add(MakeCard(contestsWrap, new Thickness(20)));

            var logWrap = new StackPanel();
            logWrap.Children.Add(new TextBlock { Text = "Telemetria & Log de Sincronização", FontSize = 14, FontWeight = FontWeights.Bold, Foreground = Theme.TextPrimary, Margin = new Thickness(0, 0, 0, 10) });
            _txtSyncLog = new TextBlock { Text = "Aguardando inicialização...", Foreground = Theme.TextSecondary, FontFamily = new FontFamily("Consolas"), FontSize = 12, TextWrapping = TextWrapping.Wrap };
            logWrap.Children.Add(_txtSyncLog);
            var logCard = MakeCard(logWrap, new Thickness(20));
            Grid.SetColumn(logCard, 2);
            bodyGrid.Children.Add(logCard);

            Grid.SetRow(bodyGrid, 2);
            grid.Children.Add(bodyGrid);

            return new Border { Child = grid };
        }

        private TextBox MakeInputBox(string defaultText, double width)
        {
            return new TextBox
            {
                Text = defaultText,
                Width = width,
                Padding = new Thickness(10, 7, 10, 7),
                Background = Theme.BgMuted,
                Foreground = Theme.TextPrimary,
                BorderBrush = Theme.BorderStrong,
                BorderThickness = new Thickness(1),
                FontSize = 13,
                FontWeight = FontWeights.SemiBold
            };
        }

        private void SwitchTab(int idx)
        {
            _activeTab = idx;
            for (int i = 0; i < _pages.Length; i++)
            {
                _pages[i].Visibility = i == idx ? Visibility.Visible : Visibility.Collapsed;
            }
            for (int i = 0; i < _navButtons.Count; i++)
            {
                bool active = i == idx;
                _navButtons[i].Background = active ? Theme.EmeraldLight : Brushes.Transparent;
                var parts = (object[])_navButtons[i].Tag;
                var icon = (System.Windows.Shapes.Path)parts[0];
                var lbl = (TextBlock)parts[1];
                icon.Stroke = active ? Theme.EmeraldDark : Theme.TextSecondary;
                lbl.Foreground = active ? Theme.EmeraldDark : Theme.TextSecondary;
                lbl.FontWeight = active ? FontWeights.Bold : FontWeights.Medium;
            }

            string[] titles = { "Gerador Inteligente", "Fechamentos C(v,k,t)", "Radar de Arbitragem E[X]", "Conferência Histórica", "Dados Oficiais Caixa" };
            string[] ctas = { "Gerar Jogos", "Calcular Fechamento", "Calcular Arbitragem", "Conferir Jogo", "Sincronizar Caixa" };
            _headerTitle.Text = titles[idx];
            _headerCta.Content = ctas[idx];
        }

        private async Task ExecuteHeaderCtaAsync()
        {
            switch (_activeTab)
            {
                case 0: await RunGerarAsync(); break;
                case 1: await RunFechamentoAsync(); break;
                case 2: await RunArbitragemAsync(); break;
                case 3: await RunBacktestAsync(); break;
                case 4: await RunSyncAsync(); break;
            }
        }

        private async Task InitializeLiveAsync()
        {
            await RunGerarAsync();
            await RunArbitragemAsync();

            var res = await _bridge.CallAsync("status");
            if (res.ContainsKey("ok") && Convert.ToBoolean(res["ok"]))
            {
                ApplyStatusPayload(res);
            }
            else
            {
                _sidebarStatusText.Text = "Modo Offline (Cache Local)";
                _sidebarStatusDot.Fill = Theme.Gold;
            }
        }

        private void ApplyStatusPayload(Dictionary<string, object> res)
        {
            int total = Convert.ToInt32(res["total_concursos"]);
            var ultimo = res.ContainsKey("ultimo") ? res["ultimo"] as Dictionary<string, object> : null;
            var paramsDict = res.ContainsKey("params") ? res["params"] as Dictionary<string, object> : null;

            if (ultimo != null)
            {
                _sidebarStatusText.Text = string.Format("Caixa Online • #{0} ({1} jogos)", ultimo["numero"], total);
            }
            else
            {
                _sidebarStatusText.Text = string.Format("Base Local • {0} concursos", total);
            }

            _openContestsPanel.Children.Clear();
            if (paramsDict != null && paramsDict.ContainsKey("concursos_abertos"))
            {
                var abertos = paramsDict["concursos_abertos"] as System.Collections.ArrayList;
                if (abertos != null)
                {
                    foreach (Dictionary<string, object> c in abertos)
                    {
                        double est = Convert.ToDouble(c["estimativa"], CultureInfo.InvariantCulture);
                        string desc = Convert.ToString(c["descricao"]);
                        string tipo = Convert.ToString(c["tipo"]);
                        string line = string.Format("#{0} {1} ({2}) — Est.: R$ {3:N0} | Sorteio: {4}",
                            c["concurso"], desc, tipo, est, c["data_hora_sorteio"]);

                        _openContestsPanel.Children.Add(new Border
                        {
                            Background = tipo == "ESPECIAL" ? Theme.GoldLight : Theme.BgMuted,
                            BorderBrush = tipo == "ESPECIAL" ? Theme.GoldBorder : Theme.Border,
                            BorderThickness = new Thickness(1),
                            CornerRadius = new CornerRadius(8),
                            Padding = new Thickness(12, 8, 12, 8),
                            Margin = new Thickness(0, 0, 0, 8),
                            Child = new TextBlock { Text = line, Foreground = Theme.TextPrimary, FontSize = 12.5, FontWeight = FontWeights.SemiBold, TextWrapping = TextWrapping.Wrap }
                        });

                        if (tipo == "ESPECIAL")
                        {
                            _viradaBadgeText.Text = est >= 1e9
                                ? string.Format("Mega da Virada #{0} • R$ {1:N2} Bi", c["concurso"], est / 1e9)
                                : string.Format("Mega da Virada #{0} • Acum. R$ {1:N1}M", c["concurso"], est / 1e6);
                        }
                    }
                }
                _txtSyncLog.Text = string.Format("[{0:HH:mm:ss}] Sincronizado com servicebus3 ({1}).\nTotal na base: {2} concursos.\nValor mínimo carrinho: R$ {3}",
                    DateTime.Now, paramsDict.ContainsKey("versao_api") ? paramsDict["versao_api"] : "online", total, paramsDict["valor_minimo_carrinho"]);
            }
            else if (ultimo != null)
            {
                double esp = ultimo.ContainsKey("valor_acumulado_especial") ? Convert.ToDouble(ultimo["valor_acumulado_especial"], CultureInfo.InvariantCulture) : 0.0;
                if (esp > 0)
                {
                    _viradaBadgeText.Text = string.Format("Mega da Virada • Acum. R$ {0:N1}M", esp / 1e6);
                }
                _txtSyncLog.Text = string.Format("[{0:HH:mm:ss}] Último concurso #{1} ({2}). Total na base: {3} concursos.",
                    DateTime.Now, ultimo["numero"], ultimo["data"], total);
            }
        }

        private async Task RunGerarAsync()
        {
            int qtd = (int)_sliderQtd.Value;
            int minS = 140, maxS = 225;
            int.TryParse(_txtMinSoma.Text, out minS);
            int.TryParse(_txtMaxSoma.Text, out maxS);

            var res = await _bridge.CallAsync("gerar", new { quantidade = qtd, modo = _selectedMode, min_soma = minS, max_soma = maxS });
            if (!res.ContainsKey("ok") || !Convert.ToBoolean(res["ok"])) return;

            var jogosArr = res["jogos"] as System.Collections.ArrayList;
            var lote = res["lote"] as Dictionary<string, object>;
            _ticketsListPanel.Children.Clear();
            _currentGeneratedGames.Clear();

            double sumScore = 0, sumDm = 0, sumEnt = 0;
            int idx = 1;
            foreach (Dictionary<string, object> item in jogosArr)
            {
                var dez = ((System.Collections.ArrayList)item["dezenas"]).Cast<object>().Select(Convert.ToInt32).ToList();
                int soma = Convert.ToInt32(item["soma"]);
                double score = Convert.ToDouble(item["score"], CultureInfo.InvariantCulture);
                double dm = Convert.ToDouble(item["mahalanobis"], CultureInfo.InvariantCulture);
                double ent = Convert.ToDouble(item["entropia"], CultureInfo.InvariantCulture);

                sumScore += score; sumDm += dm; sumEnt += ent;
                _currentGeneratedGames.Add(dez);
                _ticketsListPanel.Children.Add(CreateTicketRow(idx, dez, soma, score, true));
                if (idx == 1) HighlightVolante(dez);
                idx++;
            }

            int n = Math.Max(1, _currentGeneratedGames.Count);
            _kpiScore.Text = string.Format("{0:0.0}%", sumScore / n);
            _kpiMahalanobis.Text = string.Format("{0:0.00}", sumDm / n);
            _kpiEntropia.Text = string.Format("{0:0.0} bits", sumEnt / n);
            double custo = lote != null ? Convert.ToDouble(lote["custo_total"], CultureInfo.InvariantCulture) : n * 6.0;
            _lblGenSummary.Text = string.Format("Jogos Gerados ({0}) • Custo: R$ {1:N2}", n, custo);
        }

        private async Task RunFechamentoAsync()
        {
            if (_poolSelected.Count < 6)
            {
                MessageBox.Show("Selecione pelo menos 6 dezenas no volante.", "Cartela", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }
            _lblFechSummary.Text = "Calculando matriz otimizada no kernel nativo C# (/unsafe)...";
            var res = await _bridge.CallAsync("fechamento", new { pool = _poolSelected.OrderBy(x => x).ToArray(), garantia = _garantia });
            if (!res.ContainsKey("ok") || !Convert.ToBoolean(res["ok"]))
            {
                _lblFechSummary.Text = "Erro: " + (res.ContainsKey("error") ? res["error"] : "falha");
                return;
            }
            var jogosArr = res["jogos"] as System.Collections.ArrayList;
            var lote = res["lote"] as Dictionary<string, object>;
            _fechListPanel.Children.Clear();
            _currentFechGames.Clear();
            int idx = 1;
            foreach (Dictionary<string, object> item in jogosArr)
            {
                var dez = ((System.Collections.ArrayList)item["dezenas"]).Cast<object>().Select(Convert.ToInt32).ToList();
                int soma = Convert.ToInt32(item["soma"]);
                double score = Convert.ToDouble(item["score"], CultureInfo.InvariantCulture);
                _currentFechGames.Add(dez);
                _fechListPanel.Children.Add(CreateTicketRow(idx++, dez, soma, score, false));
            }
            double custo = lote != null ? Convert.ToDouble(lote["custo_total"], CultureInfo.InvariantCulture) : _currentFechGames.Count * 6.0;
            _lblFechSummary.Text = string.Format("Pool {0} dezenas ({1}) -> {2} volantes | Custo Oficial: R$ {3:N2}",
                _poolSelected.Count, _garantia.ToUpperInvariant(), _currentFechGames.Count, custo);
        }

        private async Task LoadLiveViradaIntoArbitragemAsync()
        {
            var res = await _bridge.CallAsync("status");
            var p = res.ContainsKey("params") ? res["params"] as Dictionary<string, object> : null;
            if (p != null && p.ContainsKey("concursos_abertos"))
            {
                foreach (Dictionary<string, object> c in (System.Collections.ArrayList)p["concursos_abertos"])
                {
                    if (Convert.ToString(c["tipo"]) == "ESPECIAL")
                    {
                        double est = Convert.ToDouble(c["estimativa"], CultureInfo.InvariantCulture);
                        _txtPremio.Text = est.ToString("0", CultureInfo.InvariantCulture);
                        await RunArbitragemAsync();
                        return;
                    }
                }
            }
            MessageBox.Show("Não foi possível obter a estimativa ao vivo da Mega da Virada no momento.", "Cartela", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private async Task RunArbitragemAsync()
        {
            double premio = 1000000000.0;
            double.TryParse(_txtPremio.Text, NumberStyles.Any, CultureInfo.InvariantCulture, out premio);
            var res = await _bridge.CallAsync("arbitragem", new { premio = premio });
            if (!res.ContainsKey("ok") || !Convert.ToBoolean(res["ok"])) return;

            var r = (Dictionary<string, object>)res["resultado"];
            string status = Convert.ToString(r["status_arbitragem"]);
            double evBruto = Convert.ToDouble(r["valor_esperado_bruto"], CultureInfo.InvariantCulture);
            double roi = Convert.ToDouble(r["roi_esperado_percent"], CultureInfo.InvariantCulture);
            double breakeven = Convert.ToDouble(r["breakeven_jackpot"], CultureInfo.InvariantCulture);
            double evAnti = Convert.ToDouble(r["ev_com_estrategia_anticolisao"], CultureInfo.InvariantCulture);
            double evSem = Convert.ToDouble(r["ev_sem_estrategia_aniversarios"], CultureInfo.InvariantCulture);
            double kellyFull = r.ContainsKey("kelly_fracao_otima_pct") ? Convert.ToDouble(r["kelly_fracao_otima_pct"], CultureInfo.InvariantCulture) : 0.0;
            double kellyQ = r.ContainsKey("kelly_quarto_pct") ? Convert.ToDouble(r["kelly_quarto_pct"], CultureInfo.InvariantCulture) : 0.0;

            _kpiArbStatus.Text = status.Split('(')[0].Trim();
            _kpiArbStatus.Foreground = roi >= 0 ? Theme.Emerald : Theme.Danger;
            _kpiArbValor.Text = string.Format("R$ {0:N2}", evBruto);
            _kpiArbRoi.Text = string.Format("{0:+0.0;-0.0;0.0}%", roi);
            _txtArbDetail.Text = string.Format(
                "• Ponto de Equilíbrio (Breakeven Jackpot): R$ {0:N2}\n" +
                "• Retorno Líquido com Anti-Colisão (dezenas > 31): E[X] = R$ {1:+0.00;-0.00}\n" +
                "• Risco com Datas de Aniversário (divisão provável): E[X] = R$ {2:+0.00;-0.00}\n" +
                "• Critério de Kelly (Edward Thorp): Kelly Full = {3:0.0000}% | Quarter-Kelly = {4:0.0000}%\n\n" +
                "Diretriz Executiva: {5}",
                breakeven, evAnti, evSem, kellyFull, kellyQ, r["diretriz_executiva"]);
        }

        private async Task RunMonteCarloAsync()
        {
            var jogo = _currentGeneratedGames.Count > 0
                ? _currentGeneratedGames[0].ToArray()
                : new int[] { 12, 14, 27, 40, 42, 45 };
            _txtArbDetail.Text = "Executando 100.000 sorteios no kernel nativo C# (/unsafe ulong*)...";
            var res = await _bridge.CallAsync("montecarlo", new { jogo = jogo, sorteios = 100000 });
            if (!res.ContainsKey("ok") || !Convert.ToBoolean(res["ok"])) return;
            var r = (Dictionary<string, object>)res["resultado"];
            var kRes = await _bridge.CallAsync("kolmogorov");
            string kolStr = "";
            if (kRes.ContainsKey("ok") && Convert.ToBoolean(kRes["ok"]))
            {
                var kr = (Dictionary<string, object>)kRes["resultado"];
                kolStr = string.Format("\n• Auditoria Kolmogorov (Incompressibilidade): Razão Real = {0} vs Controle = {1} (Incompressível: {2})",
                    kr["razao_real"], kr["razao_controle"], kr["incompressivel"]);
            }
            _txtArbDetail.Text = string.Format(
                "SIMULAÇÃO MONTE CARLO ({0:N0} sorteios em {1} ms via {2})\n" +
                "• Volante Testado: {3}\n" +
                "• Quadras: {4} ({5}% empírico vs {6}% teórico)\n" +
                "• Quinas: {7} | Senas: {8}{9}",
                Convert.ToInt64(r["sorteios"]),
                r["tempo_ms"],
                r["motor"],
                string.Join(" - ", jogo.Select(x => x.ToString("00"))),
                r["quadras"], r["taxa_quadra_pct"], r["taxa_quadra_teorica_pct"],
                r["quinas"], r["senas"], kolStr);
        }

        private async Task RunBolaoAsync()
        {
            double orc = 150.0;
            double.TryParse(_txtOrcamento.Text, NumberStyles.Any, CultureInfo.InvariantCulture, out orc);
            var res = await _bridge.CallAsync("bolao", new { orcamento = orc });
            if (!res.ContainsKey("ok") || !Convert.ToBoolean(res["ok"])) return;
            var r = (Dictionary<string, object>)res["resultado"];
            if (r.ContainsKey("erro"))
            {
                MessageBox.Show(Convert.ToString(r["erro"]), "Cartela", MessageBoxButton.OK, MessageBoxImage.Information);
                return;
            }
            var pool = ((System.Collections.ArrayList)r["pool_dezenas_selecionado"]).Cast<object>().Select(x => Convert.ToInt32(x).ToString("00"));
            var jogos = (System.Collections.ArrayList)r["jogos_gerados"];
            var sb = new StringBuilder();
            sb.AppendLine(string.Format("BOLÃO SINDICATO ÓTIMO • Orçamento: R$ {0:N2}", orc));
            sb.AppendLine(string.Format("Pool ({0} dezenas): {1}", r["tamanho_pool_recomendado"], string.Join(" - ", pool)));
            sb.AppendLine(string.Format("Volantes: {0} | Custo: R$ {1:N2} | Sobra: R$ {2:N2}",
                r["volantes_no_fechamento_garantido"], r["custo_fechamento_reais"], r["sobra_orcamento"]));
            sb.AppendLine(Convert.ToString(r["garantia_matematica"]));
            sb.AppendLine();
            int idx = 1;
            foreach (System.Collections.ArrayList j in jogos)
            {
                sb.AppendLine(string.Format("#{0:00}: {1}", idx++, string.Join("  ", j.Cast<object>().Select(x => Convert.ToInt32(x).ToString("00")))));
            }
            _txtArbDetail.Text = sb.ToString();
        }

        private async Task RunBacktestAsync()
        {
            var parts = _txtConfDezenas.Text.Replace(",", " ").Replace("-", " ").Split(new[] { ' ' }, StringSplitOptions.RemoveEmptyEntries);
            var nums = new List<int>();
            foreach (var p in parts) { int v; if (int.TryParse(p, out v)) nums.Add(v); }
            if (nums.Count != 6)
            {
                MessageBox.Show("Insira exatamente 6 dezenas válidas.", "Cartela", MessageBoxButton.OK, MessageBoxImage.Warning);
                return;
            }
            var res = await _bridge.CallAsync("backtest", new { jogo = nums.ToArray() });
            if (!res.ContainsKey("ok") || !Convert.ToBoolean(res["ok"])) return;

            var r = (Dictionary<string, object>)res["resultado"];
            _kpiQuadras.Text = Convert.ToString(r["quadras"]);
            _kpiQuinas.Text = Convert.ToString(r["quinas"]);
            _kpiSenas.Text = Convert.ToString(r["senas"]);
            _confDetailsPanel.Children.Clear();
            var detalhes = r["detalhes"] as System.Collections.ArrayList;
            if (detalhes == null || detalhes.Count == 0)
            {
                _confDetailsPanel.Children.Add(new TextBlock { Text = "Nenhuma premiação (4+ acertos) encontrada para esta combinação nos concursos registrados.", Foreground = Theme.TextMuted, FontSize = 13 });
            }
            else
            {
                foreach (Dictionary<string, object> d in detalhes)
                {
                    var dez = string.Join(" - ", ((System.Collections.ArrayList)d["sorteio"]).Cast<object>().Select(x => Convert.ToInt32(x).ToString("00")));
                    _confDetailsPanel.Children.Add(new TextBlock
                    {
                        Text = string.Format("Concurso #{0} • {1} acertos • Dezenas: {2}", d["concurso"], d["acertos"], dez),
                        Foreground = Theme.TextPrimary,
                        FontSize = 13,
                        Margin = new Thickness(0, 0, 0, 6)
                    });
                }
            }
        }

        private async Task RunSyncAsync()
        {
            _btnSync.IsEnabled = false;
            _txtSyncLog.Text = string.Format("[{0:HH:mm:ss}] Sincronizando histórico (.xlsx) e parâmetros ao vivo da Caixa...\n", DateTime.Now);
            var res = await _bridge.CallAsync("sync");
            _btnSync.IsEnabled = true;
            if (res.ContainsKey("ok") && Convert.ToBoolean(res["ok"]))
            {
                ApplyStatusPayload(res);
            }
            else
            {
                _txtSyncLog.Text += "Falha: " + (res.ContainsKey("error") ? res["error"] : "erro desconhecido");
            }
        }

        private void CopyGames(List<List<int>> jogos)
        {
            if (jogos == null || jogos.Count == 0) return;
            var sb = new StringBuilder();
            foreach (var j in jogos) sb.AppendLine(string.Join(" - ", j.Select(x => x.ToString("00"))));
            Clipboard.SetText(sb.ToString());
            MessageBox.Show(string.Format("{0} volantes copiados para a área de transferência.", jogos.Count), "Cartela", MessageBoxButton.OK, MessageBoxImage.Information);
        }

        private async Task ExportGamesAsync(string cmd, string ext, List<List<int>> jogos)
        {
            if (jogos == null || jogos.Count == 0) return;
            var dlg = new SaveFileDialog
            {
                Filter = ext == "pdf" ? "PDF (*.pdf)|*.pdf" : "CSV (*.csv)|*.csv",
                FileName = "cartela_jogos." + ext
            };
            if (dlg.ShowDialog() == true)
            {
                var res = await _bridge.CallAsync(cmd, new { jogos = jogos, filepath = dlg.FileName });
                if (res.ContainsKey("ok") && Convert.ToBoolean(res["ok"]))
                {
                    MessageBox.Show("Exportado com sucesso:\n" + dlg.FileName, "Cartela", MessageBoxButton.OK, MessageBoxImage.Information);
                }
            }
        }

        [STAThread]
        public static void Main(string[] args)
        {
            var app = new Application();
            var win = new MainWindow();
            if (args != null && args.Length >= 2 && args[0] == "--screenshot")
            {
                string outPath = args[1];
                win.ShowActivated = false;
                win.Loaded += async (s, e) =>
                {
                    await Task.Delay(3200);
                    win.UpdateLayout();
                    int w = (int)win.ActualWidth;
                    int h = (int)win.ActualHeight;
                    if (w > 0 && h > 0)
                    {
                        var rtb = new RenderTargetBitmap(w, h, 96, 96, PixelFormats.Pbgra32);
                        rtb.Render(win);
                        var enc = new PngBitmapEncoder();
                        enc.Frames.Add(BitmapFrame.Create(rtb));
                        using (var fs = new FileStream(outPath, FileMode.Create))
                            enc.Save(fs);
                    }
                    app.Shutdown();
                };
            }
            app.Run(win);
        }
    }
}
