package com.reelsaver.app

import android.Manifest
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.selection.selectable
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.DropdownMenu
import androidx.compose.material3.DropdownMenuItem
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.RadioButton
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Surface
import androidx.compose.material3.Switch
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.KeyboardType
import androidx.compose.ui.text.input.PasswordVisualTransformation
import androidx.compose.ui.text.input.VisualTransformation
import androidx.compose.ui.unit.dp
import androidx.core.content.ContextCompat
import com.reelsaver.app.data.IgMode
import com.reelsaver.app.data.Settings

class MainActivity : ComponentActivity() {

    private val notificationPermissionLauncher = registerForActivityResult(
        ActivityResultContracts.RequestPermission()
    ) { /* result ignored */ }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        maybeRequestNotifications()
        setContent {
            ReelSaverTheme {
                Surface(modifier = Modifier.fillMaxSize(), color = MaterialTheme.colorScheme.background) {
                    HomeScreen()
                }
            }
        }
    }

    private fun maybeRequestNotifications() {
        if (Build.VERSION.SDK_INT < Build.VERSION_CODES.TIRAMISU) return
        val granted = ContextCompat.checkSelfPermission(
            this, Manifest.permission.POST_NOTIFICATIONS
        ) == PackageManager.PERMISSION_GRANTED
        if (!granted) notificationPermissionLauncher.launch(Manifest.permission.POST_NOTIFICATIONS)
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
private fun HomeScreen() {
    val context = LocalContext.current
    val settings = remember { Settings(context) }

    var igMode by remember { mutableStateOf(settings.igMode) }
    var loggedInToIg by remember { mutableStateOf(settings.igCookies != null) }
    var apiKey by remember { mutableStateOf(settings.openAiApiKey.orEmpty()) }
    var apiKeyVisible by remember { mutableStateOf(false) }
    var targetLang by remember { mutableStateOf(settings.targetLanguage) }
    var autoTranscribe by remember { mutableStateOf(settings.autoTranscribe) }
    var langMenuOpen by remember { mutableStateOf(false) }

    LaunchedEffect(Unit) {
        loggedInToIg = settings.igCookies != null
        igMode = settings.igMode
    }

    Scaffold(
        topBar = { TopAppBar(title = { Text("ReelSaver") }) }
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .padding(20.dp)
                .fillMaxSize()
                .verticalScroll(rememberScrollState()),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            // ----- Tryb pobierania -----
            SectionCard(title = "Tryb pobierania (Instagram)") {
                Text(
                    "TikTok zawsze idzie wprost — wybór poniżej dotyczy tylko Instagrama.",
                    style = MaterialTheme.typography.bodySmall
                )
                Spacer(Modifier.height(12.dp))
                ModeRadioRow(
                    selected = igMode == IgMode.PUBLIC_WEB,
                    title = "Tryb publiczny (zalecany)",
                    description = "Apka otwiera w tle stronę snapinsta.app — tak jakbyś " +
                            "ręcznie wkleił link do downloadera. Bez logowania, bez ryzyka " +
                            "bana konta IG. Działa dla publicznych Reelsów.",
                    onClick = {
                        igMode = IgMode.PUBLIC_WEB
                        settings.igMode = IgMode.PUBLIC_WEB
                    }
                )
                Spacer(Modifier.height(8.dp))
                ModeRadioRow(
                    selected = igMode == IgMode.LOGGED_IN,
                    title = "Tryb zalogowany (prywatne posty)",
                    description = "Używa twojej sesji Instagrama. Pobiera też prywatne " +
                            "posty, do których masz dostęp. UWAGA: ryzyko zablokowania " +
                            "konta — używaj konta zapasowego.",
                    onClick = {
                        igMode = IgMode.LOGGED_IN
                        settings.igMode = IgMode.LOGGED_IN
                    }
                )
            }

            // ----- IG session (only relevant for logged-in mode) -----
            if (igMode == IgMode.LOGGED_IN) {
                SectionCard(title = "Instagram — logowanie") {
                    Text(
                        if (loggedInToIg) "Status: zalogowany ✓"
                        else "Status: niezalogowany — zaloguj się, żeby pobierać prywatne posty.",
                        style = MaterialTheme.typography.bodyMedium
                    )
                    Spacer(Modifier.height(12.dp))
                    Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        Button(onClick = {
                            context.startActivity(Intent(context, InstagramLoginActivity::class.java))
                        }) {
                            Text(if (loggedInToIg) "Zaloguj ponownie" else "Zaloguj się")
                        }
                        if (loggedInToIg) {
                            OutlinedButton(onClick = {
                                settings.clearInstagramSession()
                                loggedInToIg = false
                            }) { Text("Wyloguj") }
                        }
                    }
                }
            }

            // ----- Transcription -----
            SectionCard(title = "Transkrypcja") {
                Text(
                    "Po pobraniu film może zostać automatycznie przetranskrybowany " +
                            "(Whisper) i przetłumaczony (GPT-4o-mini) na wybrany język. " +
                            "Wymaga klucza OpenAI — koszty po twojej stronie.",
                    style = MaterialTheme.typography.bodySmall
                )
                Spacer(Modifier.height(12.dp))

                OutlinedTextField(
                    value = apiKey,
                    onValueChange = {
                        apiKey = it
                        settings.openAiApiKey = it
                    },
                    label = { Text("Klucz API OpenAI (sk-…)") },
                    singleLine = true,
                    modifier = Modifier.fillMaxWidth(),
                    visualTransformation = if (apiKeyVisible) VisualTransformation.None
                    else PasswordVisualTransformation(),
                    keyboardOptions = KeyboardOptions(keyboardType = KeyboardType.Password),
                    trailingIcon = {
                        IconButton(onClick = { apiKeyVisible = !apiKeyVisible }) {
                            Text(if (apiKeyVisible) "🙈" else "👁")
                        }
                    }
                )

                Spacer(Modifier.height(12.dp))

                Box {
                    OutlinedButton(
                        onClick = { langMenuOpen = true },
                        modifier = Modifier.fillMaxWidth()
                    ) {
                        Text("Język tłumaczenia: ${Settings.SUPPORTED_LANGUAGES[targetLang] ?: targetLang}")
                    }
                    DropdownMenu(
                        expanded = langMenuOpen,
                        onDismissRequest = { langMenuOpen = false }
                    ) {
                        Settings.SUPPORTED_LANGUAGES.forEach { (code, name) ->
                            DropdownMenuItem(
                                text = { Text("$name ($code)") },
                                onClick = {
                                    targetLang = code
                                    settings.targetLanguage = code
                                    langMenuOpen = false
                                }
                            )
                        }
                    }
                }

                Spacer(Modifier.height(12.dp))

                Row(verticalAlignment = Alignment.CenterVertically) {
                    Switch(
                        checked = autoTranscribe,
                        onCheckedChange = {
                            autoTranscribe = it
                            settings.autoTranscribe = it
                        }
                    )
                    Spacer(Modifier.width(12.dp))
                    Text("Transkrybuj automatycznie po pobraniu")
                }
            }

            // ----- Usage -----
            SectionCard(title = "Jak używać") {
                Text(
                    "1. W Instagramie / TikToku stuknij ikonę Udostępnij (strzałka).\n" +
                            "2. Z arkusza udostępniania Androida wybierz \"ReelSaver\".\n" +
                            "3. W trybie publicznym mignie krótkie okno strony — to normalne.\n" +
                            "4. Film zapisze się w galerii (Movies/ReelSaver).",
                    style = MaterialTheme.typography.bodyMedium
                )
            }
        }
    }
}

@Composable
private fun ModeRadioRow(
    selected: Boolean,
    title: String,
    description: String,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .selectable(selected = selected, onClick = onClick),
        verticalAlignment = Alignment.Top
    ) {
        RadioButton(selected = selected, onClick = onClick)
        Spacer(Modifier.width(8.dp))
        Column {
            Text(title, fontWeight = FontWeight.SemiBold)
            Spacer(Modifier.height(4.dp))
            Text(description, style = MaterialTheme.typography.bodySmall)
        }
    }
}

@Composable
private fun SectionCard(title: String, content: @Composable () -> Unit) {
    Card(modifier = Modifier.fillMaxWidth()) {
        Column(modifier = Modifier.padding(16.dp)) {
            Text(title, style = MaterialTheme.typography.titleLarge)
            Spacer(Modifier.height(12.dp))
            content()
        }
    }
}

@Composable
fun ReelSaverTheme(content: @Composable () -> Unit) {
    MaterialTheme(content = content)
}
